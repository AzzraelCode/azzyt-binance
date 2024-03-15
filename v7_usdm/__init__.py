"""
!!! Поддержи канал                        https://azzrael.ru/spasibo
!!! AzzraelCode YouTube                   https://www.youtube.com/@AzzraelCode

API Binance USD-M Futures
https://binance-docs.github.io/apidocs/futures/en/

Использую НЕ Официальное (но рекомендуемое в оф доке API Binance) SDK
https://github.com/binance/binance-futures-connector-python
"""
import logging
import os
from typing import Optional
from binance.um_futures import UMFutures
from helpers import floor, ceil, list_dicts, calculate_limit_price_perc, floor_by_tick_size
from diskcache import Cache

logger = logging.getLogger('azzyt-binance')
cache = Cache("cache")

class V7UsdmFutures:
    def __init__(self):
        api_key = os.getenv("BIUM_API_KEY")
        secret_key = os.getenv("BIUM_SECRET_KEY")
        if not (api_key and secret_key): raise Exception("Ключи не найдены")

        logger.debug(f"API_KEY ******{api_key[-5:]}")

        self.cl = UMFutures(key=api_key, secret=secret_key,)


    def assets(self):
        """
        Вывод доступных средств
        :return:
        """
        assets = {}
        for asset in self.cl.account().get('assets', []):
            bal = float(asset.get('walletBalance', '0.0'))
            if bal == 0.0: continue
            assets[asset.get('asset')] = bal

        logger.debug(assets)
        return assets

    def ticker_v1(self, symbol=None):
        """
        Массив всех текущих цен всех торгуемых в секции USD-M инструментов
        за 1(!) запрос и 2 лимитки
        :param symbol:
        :return:
        """
        return self.cl.ticker_price(symbol)

    def positions(self, symbol : Optional[str] = "ADAUSDT"):
        """
        Получаю текущие позиции
        :param symbol:
        :return:
        """
        positions = []
        for pos in self.cl.account().get('positions', []):
            sz = float(pos.get('positionAmt', '0.0'))
            if sz == 0.0: continue

            r = dict(
                symbol=pos.get('symbol'),
                side=('BUY', 'SELL')[sz < 0],
                rev_side=('SELL', 'BUY')[sz < 0],
                sz=sz,
                abs_sz=abs(sz),
                curr_profit=float(pos.get('unrealizedProfit', '0.0')),
            )

            logger.debug(r)

            if symbol == r['symbol']: return r
            positions.append(r)

        return positions if not symbol else None

    @cache.memoize(expire=60, ignore={0,})
    def instruments(self, quote_asset='USDT', symbol : Optional[str] = None):
        """
        Список Символов и фильтров по ним
        в тч с расчетом мин размера ордера изходя их min_qty, mon_notional, current price
        :param symbol: Можно вернуть фильтры только для одной пары
        :param quote_asset:
        :return:
        """
        logger.debug(f"instruments  {symbol}{quote_asset}")
        # текущие цены на ВСЕ торгуемые символы
        tickers = self.ticker_v1()

        symbols = []
        for s in self.cl.exchange_info().get('symbols', []):
            if s.get('status') != 'TRADING' or s.get('contractType') != 'PERPETUAL' or s.get('quoteAsset') != quote_asset:
                continue

            filters = s.get('filters')
            r = dict(
                s=s.get('symbol'),
                b=s.get('baseAsset'),
                pprice=s.get('pricePrecision'),
                pqty=s.get('quantityPrecision'),
                pbase=s.get('baseAssetPrecision'),
                pquote=s.get('quotePrecision'),
                tick_size=list_dicts(filters, 'PRICE_FILTER', 'tickSize', float),
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

            if symbol == r['s']: return r

            symbols.append(r)

        return symbols if not symbol else None

    def place_limit_order(
            self,
            symbol  = "ADAUSDT",
            side    = "BUY",
            qty     : Optional[float] = None,
            quote   : Optional[float] = None,
            price   : Optional[float] = None,
            dist    : Optional[float] = None,
    ):
        """
        Размещение лимитного ордера

        :param symbol:
        :param side: BUY / SELL
        :param qty: Размер Ордера в Базовой Валюте (BTC)
        :param quote: Размер Ордера в Котируемой Валюте (USDT)
        :param price:
        :param dist: Если цена размещения не задана, то можно разместить в %% от текущей цены исструмента
        :return:
        """
        f = self.instruments(symbol=symbol)
        logger.debug(f)

        if dist: price = floor(calculate_limit_price_perc(f['price'], side, dist), f['pprice'])
        if quote: qty = quote / price

        if not (price and qty): raise Exception("Не заданы необходимые параметры Ордера")

        args = dict(
            symbol=symbol,
            type="LIMIT",
            quantity=floor(qty, f['pqty']),
            price=floor_by_tick_size(price, f['tick_size']),
            side=side,
            timeinforce="GTC",
        )
        logger.debug(args)

        r = self.cl.new_order(**args)
        x = r.get('orderId'), r.get('status')

        logger.debug(x)
        return x

    def place_market_order(
            self,
            symbol  = "ADAUSDT",
            side    = "BUY",
            qty     : Optional[float] = None,
            quote   : Optional[float] = None,
    ):
        """
        Размещение рыночного ордера

        :param symbol:
        :param side: BUY / SELL
        :param qty: Размер Ордера в Базовой Валюте (BTC)
        :param quote: Размер Ордера в Котируемой Валюте (USDT)
        :return:
        """
        f = self.instruments(symbol=symbol)
        logger.debug(f)

        if quote: qty = quote / f['price']

        args = dict(
            symbol=symbol,
            type="MARKET",
            quantity=floor(qty, f['pqty']),
            side=side,
        )
        logger.debug(args)

        r = self.cl.new_order(**args)
        x = r.get('orderId'), r.get('status')

        logger.debug(x)
        return x

    def place_stop_loss_market_order(
            self,
            symbol="ADAUSDT",
            price: Optional[float] = None,
            dist: Optional[float] = None,
    ):
        ...

    def close_position(self, symbol="ADAUSDT"):
        """
        Закрытие открытой позы (One Way Mode)
        :param symbol:
        :return:
        """
        pos = self.positions(symbol)
        if not pos: raise Exception(f"Нет позиции по {pos}")

        args = dict(
            symbol=symbol,
            type="MARKET",
            side=pos.get('rev_side'),
            quantity=pos.get('abs_sz'),
            reduceOnly=True,
        )
        logger.debug(args)

        r = self.cl.new_order(**args)
        logger.debug(r)
        return r