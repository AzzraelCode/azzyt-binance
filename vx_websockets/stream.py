from time import sleep
import creds
import click
from binance.websocket.spot.websocket_client import SpotWebsocketClient

from vx_websockets import get_spot_client

def _kline(r):
    """
    Подписка на свечи
    :param r:
    :return:
    """
    if 'k' in r:
        print(r.get('k').get('c'), r.get('k').get('V'))
    else:
        print("Подписка kline")

def _user_data(r):
    """
    Подписка на user_data
    :param r:
    :return:
    """
    if 'e' in r:
        if r.get('e') == 'executionReport':

            id = r.get('c')
            sym = r.get('s')
            print(f"Изменились заявки {sym} / {id}")

            if r.get('X') == 'NEW':
                print("Размещение лимитки")
            elif r.get('X') == 'FILLED':
                click.secho("Заяка исполнилась, что-там дальше по страте?", fg='green')
    else:
        print("Подписка user_data")

# ******************* Основной код
click.secho("Поднимаю Stream", fg='magenta')
client = SpotWebsocketClient(stream_url="wss://testnet.binance.vision")
client.start()

try:
    listen_key = None
    # listen_key = get_spot_client().new_listen_key().get("listenKey")
    # client.user_data(listen_key=listen_key, id=1, callback=_user_data)

    # client.kline(
    #     symbol=creds.symbol,
    #     id=2,
    #     interval='1m',
    #     callback=_kline
    # )

    client.book_ticker(id=3, symbol='BTCUSDT', callback=lambda x: print(x))

    for i in range(1, 60*60*24):
        if listen_key and i % 59*60 == 0: get_spot_client().renew_listen_key(listen_key)
        if i % 60 == 0:
            click.secho(f"Сокет ок, {int(i/60)} мин.", fg="yellow")
        sleep(1)

except KeyboardInterrupt:
    ...
finally:
    client.stop()


