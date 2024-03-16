from v7_usdm import V7UsdmFutures

from helpers.Logger import setup_logger
logger = setup_logger()

if __name__ == '__main__':
    o = V7UsdmFutures()
    # o.assets()
    # o.instruments()
    # o.positions()

    # o.place_market_order(symbol="ADAUSDT", quote=7, side="SELL")
    o.place_stop_market_order(dist=5.0, is_loss=True)
    o.place_stop_market_order(dist=5.0, is_loss=False)
    # o.close_position()

    # o.place_limit_order(quote=7, side="BUY", dist=5.0)
