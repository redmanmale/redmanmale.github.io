---
layout: post
title: "Защита паролей в конфигах с помощью AES"
date: 2019-10-11
tags: csharp java windows aes
---

## Abstract

Шифруем на C#, расшифровываем на Java. Потому что надо.


## Introduction

В продолжение предыдущей [темы](https://redmanmale.com/all/programming/2019/01/27/dpapi.html).

Выяснилось, что DPAPI работает очень интересно. Если пользователь доменный, то можно зашифровать на одной машине, а расшифровать на другой. Но только если вылогиниться со всех других машин, а это максимально не наш сценарий.

В результате было решено переделать шифрование паролей на AES, с хранением ключа в файле, с ограничением к нему доступа на уровне файловой системы.


## Methods

Реализации AES есть на популярных языках, тем более на C#/Java. Однако в процессе пришлось немного поприседать.

Код довольно примитивен, из интересного. Для работы AES нужны два компонента: ключ и вектор инициализации.  
Ключ всегда одинаковый, лежит в файле.  
Вектор инициализации (IV) каждый раз новый, но для расшифровки нужен именно тот, который участвовал в шифровании. Решил хранить его вместе с шифротекстом, в начале.

### Шифруем:

```csharp
private static string Encrypt(string plain, string keyBase64)
{
    using (var aes = new AesCryptoServiceProvider
    {
        Key = Convert.FromBase64String(keyBase64),
        Mode = CipherMode.CBC
    })
    {
        aes.GenerateIV();
        var iv = aes.IV;
        using (var encryptor = aes.CreateEncryptor(aes.Key, iv))
        using (var cipherStream = new MemoryStream())
        {
            using (var tCryptoStream = new CryptoStream(cipherStream, encryptor, CryptoStreamMode.Write))
            using (var tBinaryWriter = new BinaryWriter(tCryptoStream))
            {
                cipherStream.Write(iv, 0, iv.Length);
                tBinaryWriter.Write(Encoding.UTF8.GetBytes(plain));
                tCryptoStream.FlushFinalBlock();
            }

            return Convert.ToBase64String(cipherStream.ToArray());
        }
    }
}
```

### Дешифруем

```java
private static @NotNull String decrypt( @NotNull String encryptedDataBase64, @NotNull String keyBase64 ) throws ConfigurationException
{
    int ivSize = 16;
    try
    {
        byte[] key = Base64.getDecoder().decode( keyBase64 );
        byte[] encryptedDataBytes = Base64.getDecoder().decode( encryptedDataBase64 );
        byte[] actualDataBytes = Arrays.copyOfRange( encryptedDataBytes, ivSize, encryptedDataBytes.length );
        byte[] ivBytes = Arrays.copyOfRange( encryptedDataBytes, 0, ivSize );

        Key javaKey = new SecretKeySpec( key, "AES" );
        AlgorithmParameterSpec iv = new IvParameterSpec( ivBytes );

        Cipher cipher = Cipher.getInstance( "AES/CBC/PKCS5PADDING" );
        cipher.init( Cipher.DECRYPT_MODE, javaKey, iv );

        return new String( cipher.doFinal( actualDataBytes ), StandardCharsets.UTF_8 );
    }
    catch( Exception e )
    {
        throw new ConfigurationException( Errors.PasswordDecryptionFailed, e, e.getMessage() );
    }
}
```

## Results

Код на C# был вставлен в Powershell-скрипт вместо работы с DPAPI, код на Java отправился в продукт.
