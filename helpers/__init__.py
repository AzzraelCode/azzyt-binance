import math
import os
from decimal import Decimal, ROUND_DOWN
from typing import Optional

from binance.spot import Spot
from binance.um_futures import UMFutures


def LoadSpotClient(load_keys=True) -> Spot:
    return Spot() if not load_keys else Spot(api_key=os.getenv("API_KEY"), api_secret=os.getenv("SECRET_KEY"))

def LoadUsdmFutClient(load_keys=True) -> UMFutures:
    return UMFutures() if not load_keys else UMFutures(key=os.getenv("API_KEY"), secret=os.getenv("SECRET_KEY"))

def floor(v, decimal):
    return math.floor(v * pow(10, decimal))/pow(10, decimal)

def ceil(v, decimal):
    return math.ceil(v * pow(10, decimal))/pow(10, decimal)


def list_dicts(filters_lst: list, filter_key: str, key: str, callback: Optional[callable] = None,
                  filter_field='filterType'):
    """
    Вывод значения конкретного поля конкретного фильтра + приведение типа или обработка
    В списке словарей ищу словарь где поле filter_field == filter_key
    и из этого словаря возвращаю значение в поле key
    метод подходит для фильтров инструментов, списка тикеров и проч
    :return:
    """
    r = next(x for x in filters_lst if x.get(filter_field) == filter_key).get(key)
    if callback: r = callback(r)
    return r

