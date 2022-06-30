from binance.error import ClientError
from binance.spot import Spot
import pandas as pd
from pandas import DataFrame

import creds

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

if __name__ == '__main__':
    cl = Spot(
        creds.api_key_testnet,
        creds.sec_key_testnet,
        base_url="https://testnet.binance.vision",
        proxies={ 'https': creds.proxy }
    )

    symbol = 'ETHUSDT'

    try:
        # r = cl.exchange_info(symbol)
        # print(r)

        # r = cl.new_order(
        #     symbol=symbol,
        #     newClientOrderId="azzrael_code_test_222",
        #     side='SELL',
        #     type='MARKET',
        #     quantity=1,
        #     quoteOrderQty=100,
        # )
        #
        # print(r)

        df = DataFrame(cl.get_orders(symbol, recvWindow=59000))
        print(df.head(10))
    except ClientError as e:
        print(e.error_code, e.error_message)