from time import sleep

from v7_usdm import V7UsdmFutures

from helpers.Logger import setup_logger
logger = setup_logger()

if __name__ == '__main__':
    o = V7UsdmFutures()
    # o.assets()
    # p = o.positions()
    # o.orders()
    o.pretty_symbols()

    # o.place_market_order("ADAUSDT", quote=7, side="SELL")
    # o.place_market_order("ADAUSDT", qty=10, side="BUY")
    # o.place_market_order("ADAUSDT", qty=10, side="SELL")
    # sleep(1)
    # o.place_trailing_stop("ADAUSDT", 2)

    # o.place_stop_market_order(dist=5.0, is_loss=True)
    # o.place_stop_market_order(dist=10.0, is_loss=False)

    # o.place_limit_order(quote=7, side="BUY", dist=5.0)

    # o.close_position()

