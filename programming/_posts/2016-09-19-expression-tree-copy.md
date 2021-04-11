---
layout: post
title: "Expression-tree copy"
date: 2016-09-19
tags: csharp expression-tree
---

Первый пост не тянет на rocket science, но боюсь, что если не начну с чего-то, то не начну вовсе.

Итак, представьте ситуацию (ну, вы представляйте, а я с ней столкнулся): есть некая модель данных, и в ней все объекты, кроме корневого, неизменяемые. Все интерфейсы публичные, т.е. может быть несколько реализаций. Но в процессе обработки данных модель всё же необходимо обновлять — для этого есть наши собственные реализации всех интерфейсов с доступом на запись.

Итого, что мы имеем: на вход в метод поступает объект c неизменяемыми полями, необходимо обновить какие-то поля внутри без потери старых данных.

```c#
// Корневой объект (изменяемый)
public class Data
{
    public IOtherData SomeOtherData { get; set; }

    public IAnotherData SomeAnotherData { get; set; }
}

// Неизменяемая модель
public interface IOtherData
{
    string SomeOtherStringProp { get; }

    int SomeOtherIntProp { get; }
}

public interface IAnotherData
{
    string SomeOtherStringProp { get; }

    int SomeOtherIntProp { get; }
}

// Изменяемая модель
public class OtherData : IOtherData
{
    public string SomeOtherStringProp { get; set; }

    public int SomeOtherIntProp { get; set; }
}
```

Метод обновления модели (бизнес-логика, вызывается из разных мест для обновления разных полей корневого объекта):

```c#
// Копирование тупым способом
public override void Update(Data data, string someString)
{
    var otherData = data.SomeOtherData as OtherData;
    if (otherData == null)
    {
        otherData = new OtherData
        {
            SomeOtherStringProp = data.SomeOtherData.SomeOtherStringProp,
            SomeOtherIntProp = data.SomeOtherData.SomeOtherIntProp
        };
        data.SomeOtherData = otherData;
    }

    otherData.SomeOtherStringProp = someString;
}
```

Модель ~~пока~~ не слишком большая, на несколько десятков классов. Но в дальнейшем вполне может и разрастись.

Для того, чтобы обновить данные, нужно получить из неизменяемого объекта изменяемый, не потеряв данные и обновить, что требуется.

Вариантов решения я вижу несколько:

* Оставить как есть. Куча копипасты. Плохо.

* Конструктор. Ручное копирование полей только один раз на тип пишется, но всё равно куча копипасты с приведением и проверками. Не так плохо, но плохо.

```c#
public OtherData(IOtherData iData)
{
    SomeOtherStringProp = iData.SomeOtherStringProp;
    SomeOtherIntProp = iData.SomeOtherIntProp;
}
```

Использование:

```c#
public override void Update(Data data, string someString)
{
    var otherData = data.SomeOtherData as OtherData ?? new OtherData(data.SomeOtherData);
    data.SomeOtherData = otherData;

    otherData.SomeOtherStringProp = someString;
}
```

* Статический метод в классе. Можно комбинировать с предыдущим. Приведение и проверка пишется один раз в методе, не копипастится. Лучше, но не идеально, т.к. всё равно это нужно писать для каждого типа.

```c#
public static OtherData Cast(IOtherData iOtherData)
{
    var otherData = iOtherData as OtherData;
    if (otherData == null)
    {
        otherData = new OtherData
        {
            SomeOtherStringProp = iOtherData.SomeOtherStringProp,
            SomeOtherIntProp = iOtherData.SomeOtherIntProp
        };
    }
    return otherData;
}
```

либо

```c#
public static OtherData Cast(IOtherData iOtherData)
{
    return iOtherData as OtherData ?? new OtherData(iOtherData);
}
```

Использование:

```c#
public override void Update(Data data, string someString)
{
    var otherData = OtherData.Cast(data.SomeOtherData);
    data.SomeOtherData = otherData;

    otherData.SomeOtherStringProp = someString;
}
```

* После ~~написания~~ копипасты нескольких аналогичных по смыслу кусков кода, захотелось как-то обобщить, на ум пришёл reflection.

```c#
public static class DataExtensions
{
    public static TTargetClass Cast<TSourceInterface, TTargetClass>(this TSourceInterface srcObj) 
        where TTargetClass : class, TSourceInterface, new()
    {
        if (srcObj == null)
        {
            throw new ArgumentNullException(nameof(srcObj));
        }

        var resultObj = srcObj as TTargetClass;
        if (resultObj == null)
        {
            resultObj = new TTargetClass();

            var srcObjProps = typeof(TSourceInterface).GetProperties();
            var resultObjProps = typeof(TTargetClass).GetProperties().Where(p => p.CanWrite);

            foreach (var prop in resultObjProps)
            {
                var srcObjValue = srcObjProps.First(p => p.Name.Equals(prop.Name)).GetValue(srcObj);
                prop.SetValue(resultObj, srcObjValue);
            }
        }
        return resultObj;
    }
}
```

Использование:

```c#
public override void Update(Data data, string someString)
{
    var otherData = data.SomeOtherData.Cast<IOtherData, OtherData>();
    data.SomeOtherData = otherData;

    otherData.SomeOtherStringProp = someString;
}
```

Работает. Удобно использовать, универсально. Главное замечание - скорость. Можно конечно закешировать список свойств для каждого типа, но это полумеры.


* В дело вступает expression-tree. По скорости (кроме первого для типа использования) практически не уступает первым вариантам.

```c#
public static class DataExtensions
{
    private static class DelegateHolder<TTargetClass, TSourceInterface>
        where TTargetClass : class, TSourceInterface, new()
    {
        public static readonly Func<TSourceInterface, TTargetClass> InternalCast = CreateInternalCast();

        private static Func<TSourceInterface, TTargetClass> CreateInternalCast()
        {
            var srcObjProps = typeof(TSourceInterface).GetProperties();
            var resultObjProps = typeof(TTargetClass).GetProperties();

            var sourceParam = Expression.Parameter(typeof(TSourceInterface));
            var resultParam = Expression.Variable(typeof(TTargetClass));

            var body = new List<Expression>(srcObjProps.Length + 2)
            {
                Expression.Assign(resultParam, Expression.New(resultParam.Type)),
            };

            var propNames = from srcInfo in srcObjProps
                            join res in resultObjProps on srcInfo.Name equals res.Name
                            where srcInfo.CanRead && res.CanWrite
                            select res.Name;

            foreach (var propName in propNames)
            {
                body.Add(Expression.Assign(Expression.Property(resultParam, propName), Expression.Property(sourceParam, propName)));
            }

            body.Add(resultParam);

            var block = Expression.Block(new[] { resultParam }, body);
            var lambda = Expression.Lambda(block, sourceParam);
            var compiledLambda = (Func<TSourceInterface, TTargetClass>)lambda.Compile();

            return compiledLambda;
        }
    }

    /// <summary>
    /// Быстрое копирование через expression Tree
    /// </summary>
    public static TTargetClass Cast<TSourceInterface, TTargetClass>(this TSourceInterface srcObj) 
        where TTargetClass : class, TSourceInterface, new()
    {
        if (srcObj == null)
        {
            throw new ArgumentNullException(nameof(srcObj));
        }

        return srcObj as TTargetClass ?? DelegateHolder<TTargetClass, TSourceInterface>.InternalCast(srcObj);
    }
}
```

Использование не изменилось:

```c#
public override void Update(Data data, string someString)
{
    var otherData = data.SomeOtherData.Cast<IOtherData, OtherData>();
    data.SomeOtherData = otherData;

    otherData.SomeOtherStringProp = someString;
}
```

Единственное неудобство, что приходится передавать оба типа, хотя ```TSourceInterface``` шарп мог бы и сам вывести.

Весь код лежит на [гитхабе][github-rep].

[github-rep]: https://github.com/redmanmale/ExpressionTreeCopy
