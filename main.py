from v7_usdm import V7UsdmFutures

from helpers.Logger import setup_logger
logger = setup_logger()

if __name__ == '__main__':
    o = V7UsdmFutures()
    # o.assets()
    # o.instruments()
    # o.place_limit_order(quote=7, side="BUY", dist=5.0)
    # o.place_market_order(symbol="ADAUSDT", quote=7, side="BUY")
    # o.place_stop_loss_market_order()
    # o.positions()
    o.close_position()
