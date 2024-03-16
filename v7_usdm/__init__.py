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

            # logger.debug(pos)

            r = dict(
                symbol=pos.get('symbol'),
                side=('BUY', 'SELL')[sz < 0],
                side_sign=(1.0, -1.0)[sz<0],
                rev_side=('SELL', 'BUY')[sz < 0],
                sz=sz,
                abs_sz=abs(sz),
                curr_profit=float(pos.get('unrealizedProfit', '0.0')),
                price=float(pos.get('entryPrice', '0.0')),
                leverage=float(pos.get('leverage', '0.0')),
            )
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
        # Получаю текущую позицию по инструменту
        pos = self.positions(symbol)
        if not pos: raise Exception(f"Нет позиции по {pos}")
        logger.debug(pos)

        # Получаю фильтры инструмента (точности, лимиты, текущую цену)
        f = self.instruments(symbol=symbol)
        logger.debug(f)

        # расчет stopPrice по дистанции
        if dist:
            from_price = (f['price'], pos['price'])[dist_from_entry] # от какой цены считать - цены позы или тек цены инструмента
            logger.debug(from_price)
            price = calculate_limit_price_perc(
                from_price,
                pos['rev_side'],
                (-1, 1)[is_loss]*pos['side_sign']*dist # STOP_LOSS/TAKE_PROFIT, Pos Side
            )

        args = dict(
            symbol=symbol,
            type=("TAKE_PROFIT_MARKET", "STOP_MARKET")[is_loss],
            side=pos.get('rev_side'),
            closePosition=True,
            stopPrice=floor_by_tick_size(price, f['tick_size']),
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