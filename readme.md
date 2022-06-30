# Работа с API Binance

Исходный код для видео на канале Azzrael Code / https://azzrael.ru.

## Основные ссылки
- Рефералка для реги на Binance https://accounts.binance.com/ru/register?ref=335216425
- https://binance-docs.github.io/apidocs/spot/en/#general-info
- https://github.com/binance/binance-connector-python
- https://testnet.binance.vision/

## Для TestNet

- Нужен GitHub аккаунт.
- Нельзя сбросить акк или пополнить виртуальные деньги (сбрасывается раз в мес, неожиданно).

## Лимиты

https://binance-docs.github.io/apidocs/spot/en/#limits


## Проблемы

### Ошибки времени сервера ( реально бесит ;) )
```shell script
Timestamp for this request was 1000ms ahead of the server's time
Timestamp for this request is outside of the recvWindow
```
- https://github.com/ccxt/ccxt/issues/936
- Установи время и дублируй запросы

### Сертификаты

Только на вебсокетах
- https://github.com/binance/binance-connector-python/issues/57

pip install certifi
Get the file path of cacert.pem file by running python -m certifi
Copy the file path of cacert.pem and set the Environment Variables for SSL_CERT_FILE. These are the steps to setup environment variable on windows.
Restart IDE and run the websocket example

### Рестарт вебсокета

На данный момент сокет нужно рестартить рах в 24 часа. Однако в binance-connector-python
используется twisted.reactor, а его нельзя перезапустить в одном процессе
https://github.com/binance/binance-connector-python/issues/114
Т.е. скрипт питона поднимающий вебсокет нужно прибивать (чтобы прибить процесс => прибить реактор),
а затем поднимать вновь. Но в любом сл нужен какой-то внешний, надежный сервис для контроля скрипта (типа supervisord).