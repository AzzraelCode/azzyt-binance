"""
!!! Поддержи канал                        https://azzrael.ru/spasibo
!!! AzzraelCode YouTube                   https://www.youtube.com/@AzzraelCode

API Binance USD-M Futures
https://binance-docs.github.io/apidocs/futures/en/

Использую НЕ Официальное (но рекомендуемое в оф доке API Binance) SDK
https://github.com/binance/binance-futures-connector-python
"""

import os
from typing import Optional

from binance.um_futures import UMFutures
from helpers import floor, ceil, list_dicts


class V7UsdmFutures:
    def __init__(self):
        self.cl = UMFutures(key=os.getenv("API_KEY"), secret=os.getenv("SECRET_KEY"))

    def assets(self):
        """
        Вывод доступных средств
        :return:
        """
        for asset in self.cl.account().get('assets', []):
            bal = float(asset.get('walletBalance', '0.0'))
            if bal == 0.0: continue
            print(asset.get('asset'), bal)

    def ticker_v1(self, symbol=None):
        """
        Массив всех текущих цен всех торгуемых в секции USD-M инструментов
        за 1(!) запрос и 2 лимитки
        :param symbol:
        :return:
        """
        return self.cl.ticker_price(symbol)

    def instruments(self, quote_asset='USDT'):
        """
        Список Символов и фильтров по ним
        в тч с расчетом мин размера ордера изходя их min_qty, mon_notional, current price
        :param quote_asset:
        :return:
        """
        # текущие цены на ВСЕ торгуемые символы
        tickers = self.ticker_v1()

        for s in self.cl.exchange_info().get('symbols', []):
            if s.get('status') != 'TRADING' or s.get('contractType') != 'PERPETUAL' or s.get(
                    'quoteAsset') != quote_asset:
                continue

            filters = s.get('filters')
            r = dict(
                s=s.get('symbol'),
                b=s.get('baseAsset'),
                pprice=s.get('pricePrecision'),
                pqty=s.get('quantityPrecision'),
                pbase=s.get('baseAssetPrecision'),
                pquote=s.get('quotePrecision'),
            )

            r['price'] = list_dicts(tickers, r['s'], 'price', float, 'symbol')

            # считаю минимальный размер ордера
            # кот зависит от сочетания MIN_NOTIONAL / LOT_SIZE и текущей цены,
            # с округлением итогого значения в qty precision
            min_not = list_dicts(filters, 'MIN_NOTIONAL', 'notional', float)
            min_qty = list_dicts(filters, 'LOT_SIZE', 'minQty', float)
            lot_by_qty = min_qty * r['price']
            # здесь НЕЛЬЗЯ округлять вниз - иначе из-за окр итоговое значение может стать меньше MIN_NOTIONAL|LOT_SIZE
            r['min_quote'] = ceil((min_not, lot_by_qty)[min_not <= lot_by_qty], r['pquote'])
            r['min_qty'] = ceil(r['min_quote'] / r['price'], r['pqty'])

            print(r)
