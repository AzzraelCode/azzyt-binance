'''
1 Create blank main.py
2 go to https://binance-docs.github.io/apidocs/spot/en/#introduction
3 Install https://github.com/binance/binance-connector-python
4 Get Binance API Keys https://www.youtube.com/watch?v=mggpY1rJEp8
5 Load API Keys
6 Create Spot Client
7 Get Orders
8 Make Orders Unique
9 Install https://openpyxl.readthedocs.io/en/stable/tutorial.html
10 Some pretties
'''

import os
from datetime import datetime
from time import sleep

from binance.spot import Spot
from openpyxl.workbook import Workbook

SYMBOL = "BTCUSDT"
API_KEY = os.getenv("API_KEY", "DONOT-HARDCODE-KEYS")
SECRET_KEY = os.getenv("SECRET_KEY", "UNSAFELY")

if __name__ == '__main__':
    print(f"Hola, AzzraelCode YouTube Subs!")

    # * Create Spot Client
    cl = Spot(api_key=API_KEY, api_secret=SECRET_KEY)

    orders_dict = {} # just for unique by orderId
    last_order_time = None
    for p in range(0, 100500): # while True: # can be replaced
        orders_page = cl.get_orders(symbol=SYMBOL, endTime=last_order_time, limit=1000) # paginating back in time
        if len(orders_page) < 1: break # empty

        # * pagination routines
        last_order_at_page = orders_page[0]
        if last_order_time == last_order_at_page['time']: break # last page
        last_order_time = last_order_at_page['time'] # important for pagination

        # * unique orders by orderId
        for order in orders_page:
            # parse timestamps for pretty datetime
            for timed in ['time', 'updateTime', 'workingTime', 'trailingTime']:
                order[timed] = datetime.fromtimestamp(order[timed]/1000) if timed in order and order[timed] > 0 else ""

            # drop some useless fields (for me) fields
            for f in ['icebergQty', 'timeInForce', 'selfTradePreventionMode']:
                del order[f]

            # add some fields if not exists in order
            for f in ['trailingDelta']:
                if f not in order:
                    order[f] = "-"

            orders_dict[order['orderId']] = order

        # * limits routines: Weight(IP): 10 with symbol of 12000 limits per minute ~ 20 query per sec
        sleep(0.06)
        print(f"{p} page")

    # * flatten dict to list
    orders_list = list(orders_dict.values())
    print(f"Finished w {p} pages, {len(orders_list)}")

    # * store to excel
    wb = Workbook() # create Workbook
    ws = wb.active # select sheet
    # or hardcode from response https://binance-docs.github.io/apidocs/spot/en/#all-orders-user_data
    # or u can skip useless for u
    headers = list(orders_list[0].keys())
    ws.append(headers) # add headers first
    for order in orders_list: # adding rows
        # * order content can be different (trailing, strategy etc...)
        row = [order[h] if h in order else "-" for h in headers]
        ws.append(row)

    wb.save("orders.xlsx") # save file
    print("Saved")