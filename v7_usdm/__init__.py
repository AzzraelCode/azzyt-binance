"""
!!! Поддержи канал                        https://azzrael.ru/spasibo
!!! AzzraelCode YouTube                   https://www.youtube.com/@AzzraelCode
!!! Рефералка для Binance                 https://accounts.binance.com/ru/register?ref=335216425

API Binance USD-M Futures
https://binance-docs.github.io/apidocs/futures/en/

Использую НЕ Официальное (но рекомендуемое в оф доке API Binance) SDK
https://github.com/binance/binance-futures-connector-python
"""
import logging
import os
from typing import Optional
from binance.um_futures import UMFutures
from pandas import DataFrame

from helpers import floor, ceil, list_dicts, calculate_limit_price_perc, floor_by_tick_size
from diskcache import Cache

logger = logging.getLogger('azzyt-binance')
cache = Cache("cache")

class Position:

    def __init__(self, pos : dict):
        # logger.debug(pos)

        self.qty = float(pos.get('positionAmt', '0.0'))
        self.symbol = pos.get('symbol')
        self.side = ('BUY', 'SELL')[self.qty < 0]
        self.side_sign = (1.0, -1.0)[self.qty < 0]
        self.rev_side = ('SELL', 'BUY')[self.qty < 0]
        self.abs_qty = abs(self.qty)
        self.curr_profit = float(pos.get('unrealizedProfit', '0.0'))
        self.price = float(pos.get('entryPrice', '0.0'))
        self.leverage = float(pos.get('leverage', '0.0'))

    def __str__(self):
        return str(self.__dict__)

class Symbol:
    def __init__(self, s: dict, tickers : list):
        filters = s.get('filters')
        self.s=s.get('symbol')
        self.b=s.get('baseAsset')
        self.pprice=s.get('pricePrecision')
        self.pqty=s.get('quantityPrecision')
        self.pbase=s.get('baseAssetPrecision')
        self.pquote=s.get('quotePrecision')
        self.tick_size=list_dicts(filters, 'PRICE_FILTER', 'tickSize', float)

        self.price = list_dicts(tickers, self.s, 'price', float, 'symbol')

        # считаю минимальный размер ордера
        # кот зависит от сочетания MIN_NOTIONAL / LOT_SIZE и текущей цены,
        # с округлением итогого значения в qty precision
        self.min_notional = list_dicts(filters, 'MIN_NOTIONAL', 'notional', float)
        self.min_qty_filter = list_dicts(filters, 'LOT_SIZE', 'minQty', float)
        lot_by_qty = self.min_qty_filter * self.price
        # здесь НЕЛЬЗЯ округлять вниз - иначе из-за окр итоговое значение может стать меньше MIN_NOTIONAL|LOT_SIZE
        self.min_quote = ceil((self.min_notional, lot_by_qty)[self.min_notional <= lot_by_qty], self.pquote)
        self.min_qty = ceil(self.min_quote / self.price, self.pqty)

    def __str__(self):
        return str(self.__dict__)

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

    @cache.memoize(expire=30, ignore={0, })
    def ticker_v1(self, symbol=None):
        """
        Массив всех текущих цен всех торгуемых в секции USD-M инструментов
        за 1(!) запрос и 2 лимитки
        :param symbol:
        :return:
        """
        return self.cl.ticker_price(symbol)

    def positions(self, symbol : Optional[str] = "ADAUSDT") -> Position | list[Position]:
        """
        Получаю текущие позиции
        :param symbol:
        :return:
        """
        positions = []
        for pos in self.cl.account().get('positions', []):
            sz = float(pos.get('positionAmt', '0.0'))
            if sz == 0.0: continue
            r = Position(pos)

            if symbol == r.symbol: return r
            positions.append(r)

        return positions if not symbol else None

    def orders(self, symbol : Optional[str] = "ADAUSDT"):
        orders = self.cl.get_orders(symbol=symbol)
        logger.debug(orders)

    @cache.memoize(expire=60, ignore={0,})
    def symbols(self, quote_asset='USDT', symbol : Optional[str] = None):
        """
        Список Символов и фильтров по ним
        в тч с расчетом мин размера ордера изходя их min_qty, mon_notional, current price
        :param symbol: Можно вернуть фильтры только для одной пары
        :param quote_asset:
        :return:
        """
        # текущие цены на ВСЕ торгуемые символы
        tickers = self.ticker_v1()

        symbols = []
        for s in self.cl.exchange_info().get('symbols', []):
            if s.get('status') != 'TRADING' or s.get('contractType') != 'PERPETUAL' or s.get('quoteAsset') != quote_asset: continue
            r = Symbol(s, tickers)

            if symbol == r.s: return r
            symbols.append(r)

        return symbols if not symbol else None

    @cache.memoize(expire=60, ignore={0, })
    def change24h(self):
        """
        Получение суточных объемов и изм цены
        Weight 40 !!!
        :return:
        """
        return {s.get('symbol') : dict(
            s=s.get('symbol'),
            priceChangePercent=float(s.get('priceChangePercent')),
            priceChange=float(s.get('priceChange')),
            lastPrice=float(s.get('lastPrice')),
            volume=float(s.get('volume')),
            quoteVolume=float(s.get('quoteVolume')),
        ) for s in self.cl.ticker_24hr_price_change()}

    def pretty_symbols(self, quote_asset='USDT', symbol : Optional[str] = None):
        changes = self.change24h()
        symbols = self.symbols(quote_asset, symbol)

        df = DataFrame([{**s.__dict__, **changes.get(s.s, {})} for s in symbols])
        df.to_csv('../data/pretty_symbols.csv', index=False)
        # print(df)
        return df


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
        s = self.symbols(symbol=symbol)
        if dist: price = floor(calculate_limit_price_perc(s.price, side, dist), s.pprice)
        if quote: qty = quote / price

        if not (price and qty): raise Exception("Не заданы необходимые параметры Ордера")

        args = dict(
            symbol=symbol,
            type="LIMIT",
            quantity=floor(qty, s.pqty),
            price=floor_by_tick_size(price, s.tick_size),
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
        s = self.symbols(symbol=symbol)
        if quote: qty = quote / s.price

        args = dict(
            symbol=symbol,
            type="MARKET",
            quantity=floor(qty, s.pqty),
            side=side,
        )
        logger.debug(args)

        r = self.cl.new_order(**args)
        x = r.get('orderId'), r.get('status')

        logger.debug(x)
        return x

    def place_stop_market_order(
            self,
            symbol="ADAUSDT",
            price: Optional[float] = None,
            dist: Optional[float] = None,
            dist_from_entry : bool = True,
            is_loss: bool = True,
    ):
        """
        Установка РЫНОЧНЫХ стоп ордеров (STOP_MARKET / TAKE_PROFIT_MARKET)
        на закрытие всей позы полностью по указанному Инструменту
        ! Для One Way Mode

        :param symbol:
        :param price: stopPrice
        :param dist: Проценты, дистанция от цены для расчетацены поставновки стопа (stopPrice)
        :param dist_from_entry: True == Считать дистанцию стопа от входа в позу, False == текущей цены инструмента
        :param is_loss: True == STOP_MARKET, False == TAKE_PROFIT_MARKET
        :return:
        """
        pos, s = self.get_position_w_filters(symbol)

        # расчет stopPrice по дистанции
        if dist:
            from_price = (s.price, pos.price)[dist_from_entry] # от какой цены считать - цены позы или тек цены инструмента
            logger.debug(from_price)
            price = calculate_limit_price_perc(
                from_price,
                pos.side,
                (-1, 1)[is_loss]*pos.side_sign*dist # STOP_LOSS/TAKE_PROFIT, Pos Side
            )

        args = dict(
            symbol=symbol,
            type=("TAKE_PROFIT_MARKET", "STOP_MARKET")[is_loss],
            side=pos.rev_side,
            closePosition=True,
            stopPrice=floor_by_tick_size(price, s.tick_size),
        )
        logger.debug(args)

        r = self.cl.new_order(**args)
        logger.debug(r)
        return r

    def place_trailing_stop(
            self,
            symbol,
            dist : float,
            dist_activate : Optional[float] = None,
    ):
        pos, s = self.get_position_w_filters(symbol)
        # activate_price = calculate_limit_price_perc(pos.price, pos.rev_side, -1*pos.side_sign * dist_activate) if dist_activate else None

        args = dict(
            symbol=symbol,
            callbackRate=dist,
            type="TRAILING_STOP_MARKET",
            side=pos.rev_side,
            quantity=pos.abs_qty,
        )
        logger.debug(args)

        r = self.cl.new_order(**args)
        logger.debug(r)
        return r

    def close_position(self, symbol="ADAUSDT"):
        """
        Закрытие открытой позы (One Way Mode)
        :param symbol:
        :return:
        """
        pos = self.positions(symbol)
        if not pos: raise Exception(f"Нет позиции по {symbol}")

        args = dict(
            symbol=symbol,
            type="MARKET",
            side=pos.rev_side,
            quantity=pos.abs_qty,
            reduceOnly=True,
        )
        logger.debug(args)

        r = self.cl.new_order(**args)
        logger.debug(r)
        return r

    def get_position_w_filters(self, symbol = "ADAUSDT"):
        # Получаю текущую позицию по инструменту
        pos = self.positions(symbol)
        if not pos: raise Exception(f"Нет позиции по {pos}")
        logger.debug(pos)

        # Получаю фильтры инструмента (точности, лимиты, текущую цену)
        f = self.symbols(symbol=symbol)
        logger.debug(f)

        return pos, f