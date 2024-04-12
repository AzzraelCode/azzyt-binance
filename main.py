from time import sleep

import pandas as pd
from pandas import DataFrame

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from v7_usdm import V7UsdmFutures

from helpers.Logger import setup_logger
logger = setup_logger()

if __name__ == '__main__':
    o = V7UsdmFutures()
    # o.assets()
    # p = o.positions()
    # o.orders()

    df = o.pretty_symbols()[['s', 'min_qty_filter', 'min_notional', 'min_qty', 'price', 'min_quote']]
    print(df)

    # Получаю суточные изменения цены и объема в один запрос
    # df : DataFrame = DataFrame(o.change24h().values(), columns=['s', 'priceChangePercent', 'quoteVolume'])
    # df['changePercAbs'] = df['priceChangePercent'].abs()
    # print(
    #     df[(df['quoteVolume'] > 500000000) & (df['changePercAbs'] > 5.0)]
    #         .sort_values(by=['changePercAbs'], ascending=False)
    # )

    # o.place_market_order("ADAUSDT", quote=7, side="SELL")
    # o.place_market_order("ADAUSDT", qty=10, side="BUY")
    # o.place_market_order("ADAUSDT", qty=10, side="SELL")
    # sleep(1)
    # o.place_trailing_stop("ADAUSDT", 2)

    # o.place_stop_market_order(dist=5.0, is_loss=True)
    # o.place_stop_market_order(dist=10.0, is_loss=False)

    # o.place_limit_order(quote=7, side="BUY", dist=5.0)

    # o.close_position()

