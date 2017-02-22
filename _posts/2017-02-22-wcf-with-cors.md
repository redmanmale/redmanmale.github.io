---
layout: post
title:  "WCF service with CORS"
date:   2017-02-22
categories: c# wcf rest cors
permalink: wcf-with-cors
---

## Abstract

Компактная и функциональная реализация механизма CORS для WCF REST сервиса.

## Introduction

В одном проекте, в котором я принимал участие, в качестве интерфейса пользователя использовалась Кибана, а весь кастомный функционал писался в виде плагинов к ней. Кибана для повышения безопасности использует механизм CORS (Cross-Origin Resource Sharing).

Я же занимался бэкендом в целом и API для этих плагинов в частности. И для их корректной работы требовалось включить CORS для этих WCF сервисов.

Как выяснилось, это весьма нетривиально, поскольку из коробки WCF такого не предоставляет, а многочисленные советы/решения нагугленные в интернетах либо не работали вовсе, либо были чересчур громоздкими и накладывали ограничения.

В итоге из нескольких различных источников было собрано достаточно элегантное и компактное, но полностью работоспособное решение.

## Methods

На старте мы имеем интерфейс и реализующий его сервис:

```csharp
[ServiceContract]
public interface IService
{
    [OperationContract]
    [WebInvoke(Method = "GET", UriTemplate = "something", ResponseFormat = WebMessageFormat.Json)]
    string GetSomthing();
}

[ServiceBehavior(InstanceContextMode = InstanceContextMode.Single, IncludeExceptionDetailInFaults = true)]
public class Service : IService
{
    public string GetSomthing()
    {
        return "Hello!";
    }
}
```

Для запуска используем:

```csharp
var service = new Service();
var host = new WebServiceHost(service, new Uri("http://127.0.0.1:8090"));
host.Open();
```

#### Взгляд с другой стороны (плагин в Кибане)
Плагин (или Кибана) делает два запроса, первый это OPTIONS:

```
Access-Control-Request-Method: GET
Access-Control-Request-Headers: kbn-version
Origin: http://127.0.0.1:5602
```

второй это сам GET-запрос на получение данных:

```
kbn-version: 5.1.1
Origin: http://10.34.90.78:5602
```

Запускаем сервис, шлём запросы (Fiddler'ом или башовым curl'ом).  
И видим, что ничего не работает: `Status code: 405 Method not allowed`

Начинаем исправлять.  
Для модификации заголовков ответа сервиса, нам понадобится `CustomHeaderMessageInspector`:

```csharp
public class CustomHeaderMessageInspector : IDispatchMessageInspector
{
    private readonly IReadOnlyDictionary<string, string> _requiredHeaders;

    public CustomHeaderMessageInspector(Dictionary<string, string> headers)
    {
        _requiredHeaders = headers ?? new Dictionary<string, string>();
    }

    public object AfterReceiveRequest(ref Message request, IClientChannel channel, InstanceContext instanceContext)
    {
        return null;
    }

    public void BeforeSendReply(ref Message reply, object correlationState)
    {
        var httpHeader = reply.Properties["httpResponse"] as HttpResponseMessageProperty;
        foreach (var item in _requiredHeaders)
        {
            httpHeader?.Headers.Add(item.Key, item.Value);
        }
    }
}
```

Реализуем CORS-поведение:

```csharp
public class EnableCorsBehavior : BehaviorExtensionElement, IEndpointBehavior
{
    public void AddBindingParameters(ServiceEndpoint endpoint, BindingParameterCollection bindingParameters) { }

    public void ApplyClientBehavior(ServiceEndpoint endpoint, ClientRuntime clientRuntime) { }

    public void ApplyDispatchBehavior(ServiceEndpoint endpoint, EndpointDispatcher endpointDispatcher)
    {
        var requiredHeaders = new Dictionary<string, string>
        {
            {"Access-Control-Allow-Origin", "*"},
            {"Access-Control-Request-Method", "POST,GET,PUT,DELETE,OPTIONS"},
            {"Access-Control-Allow-Headers", "Origin,X-Requested-With,Content-Type,Accept,Authorization"}
        };
        endpointDispatcher.DispatchRuntime.MessageInspectors.Add(new CustomHeaderMessageInspector(requiredHeaders));
    }

    public void Validate(ServiceEndpoint endpoint) { }

    public override Type BehaviorType
    {
        get { return typeof(EnableCorsBehavior); }
    }

    protected override object CreateBehavior()
    {
        return new EnableCorsBehavior();
    }
}
```

Добавляем новое поведение ко всем endpoint'ам и запускаем:

```csharp
var host = new WebServiceHost(service);
host.AddServiceEndpoint(typeof(IService), new WebHttpBinding(), new Uri("http://127.0.0.1:8090"));
foreach (var endpoint in host.Description.Endpoints)
{
    endpoint.Behaviors.Add(new EnableCorsBehavior());
}
host.Open();
```

Шлём запрос и видим ту же картину: `Status code: 405 Method not allowed`

Всё не так просто. Нужно сделать так, чтобы наш сервис отвечал на первый запрос Кибаны (OPTIONS). В интерфейс сервиса добавляем:

```csharp
[OperationContract]
[WebInvoke(Method = "OPTIONS", UriTemplate = "*")]
void GetOptions();
```

и реализуем в сервисе:

```csharp
public void GetOptions() { }
```

Запускаем, пробуем и... nope. Вроде `200 OK`, но ничего не работает.

А всё потому, что Кибана не получила свой заголовок, поэтому ничего и не сделала.  
Добавляем в список заголовков ответа `kbn-version`.

Пробуем снова и всё наконец хорошо!

## Results

Приведённый выше подход позволяет без особого геморроя включить CORS для любого сервиса и комбинировать это поведение с другими.  
Код на [гитхабе][wcf-with-cors].

[wcf-with-cors]: https://github.com/redmanmale/WcfWithCors
