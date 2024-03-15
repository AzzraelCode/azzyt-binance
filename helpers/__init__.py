import math
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import Optional

def floor_by_tick_size(v, tick_size):
    return float(Decimal(v).quantize(Decimal(str(tick_size)), rounding=ROUND_DOWN))

def ceil_by_tick_size(v, tick_size):
    return float(Decimal(v).quantize(Decimal(str(tick_size)), rounding=ROUND_UP))

def floor(v, decimal):
    # return math.floor(v * pow(10, decimal))/pow(10, decimal)
    if decimal == 0: return float(int(v))
    return float(Decimal(v).quantize( Decimal(str(1 / (10**decimal))), rounding=ROUND_DOWN))

def ceil(v, decimal):
    # return math.ceil(v * pow(10, decimal))/pow(10, decimal)
    return float(Decimal(v).quantize( Decimal(str(1 / (10**decimal))), rounding=ROUND_UP))


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

def calculate_limit_price_perc(price, side : str = "SELL", distance_perc : float = 2.0):
    """
    Расчет цен для постановки лимитного/алго ордера
    в процентах от заданной цены
    и в зависимости от направления
    :param price: Цена инструмента
    :param side: Sell/Buy
    :param distance_perc: колво процентов, мб отрицательным
    :return:
    """
    return price * (100 + ((-1, 1)[side.lower() == "sell"] * distance_perc)) / 100