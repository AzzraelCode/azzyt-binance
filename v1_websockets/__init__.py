import logging
import creds

from binance.spot import Spot

import pandas as pd
pd.set_option('display.max_rows', 5000)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

from binance.lib.utils import config_logging
config_logging(logging, logging.CRITICAL)

def get_spot_client():
    """
    Функция для инициализации спотового клиента
    для Тестнета binance
    :return:
    """
    return Spot(
        base_url='https://testnet.binance.vision',
        key=creds.api_key_testnet,
        secret=creds.sec_key_testnet,
    )