from datetime import datetime

from binance.error import ClientError
from binance.spot import Spot
import pandas as pd
from pandas import DataFrame

import creds

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

'''
# Содержание: LIMIT_ORDER / Лимитная заявка

- Чем отличается лимитная заявка от рыночной https://academy.binance.com/ru/articles/what-is-a-limit-order
- Как создать лимитную заявку, какие параметры необходимы в new_order
- Что значит "Исполнится по лучшей цене" и как зависит от направления
- Как отменить не исполненную заявку cancel_order
- Ошибки фильтров PERCENT_PRICE, LOT_SIZE, MIN_NOTIONAL https://binance-docs.github.io/apidocs/spot/en/#filters
- Как определить лучшую цену для лимитной заявки в API Binance book_ticker
- Частично исполненная лимитная заявка PARTIALLY_FILLED
- Что значит аргумент timeInForce и как его использовать, IOC FOK GTC https://www.binance.com/en-IN/support/faq/5d3fa5e5709f47e0b5f186b350da1655

# О чем НЕ будет в этом видео, но может быть в следующих

- Iceberg Order
- Алгоритмические ордера (Stop [Limit] Order, Stop Loss [Limit] Order, Take Profit [Limit] Order)
'''


if __name__ == '__main__':

    cl = Spot(
        creds.api_key_testnet,
        creds.sec_key_testnet,
        base_url="https://testnet.binance.vision",
        proxies={ 'https': creds.proxy }
    )

    symbol = 'BTCUSDT'

    try:

        # print(f"* exchange_info {symbol}* ", cl.exchange_info(symbol), sep="\n")

        # print(f"* best_price {symbol}* ", cl.book_ticker(symbol=symbol), sep="\n")
        # buy_price = cl.book_ticker(symbol=symbol).get('askPrice')
        # sell_price = cl.book_ticker(symbol=symbol).get('bidPrice')


        print(cl.new_order(
            symbol=symbol,
            # newClientOrderId="sell_btcusdt_15",
            side='SELL',
            type='LIMIT',
            quantity=0.7,

            price=30000,
            timeInForce='GTC'
        ))

        print(f"* account assets * ", cl.account(), sep="\n")

        # order_id = 8214572
        # print(f"* CANCEL order {order_id}", cl.cancel_order(symbol=symbol, orderId=order_id), sep="\n")

        df = DataFrame(cl.get_orders(symbol, recvWindow=59000), columns=['price', 'origQty', 'executedQty', 'cummulativeQuoteQty', 'origQuoteOrderQty', 'status', 'type', 'side', 'orderId'])
        print("* ORDERS *", df.tail(10), sep="\n")
    except ClientError as e:
        print(e.error_code, e.error_message)


















