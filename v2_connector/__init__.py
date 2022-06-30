from binance.spot import Spot

import creds

# https://binance-docs.github.io/apidocs/spot/en/#api-library
# https://github.com/binance/binance-connector-python

cl = Spot(show_header=True)
r = cl.time()
# r = cl.klines("BTCUSDT", "1m", limit=1000)

print(r)

# cl = Spot(key=creds.api_key_testnet, secret=creds.sec_key_testnet, base_url='https://testnet.binance.vision')
# print(cl.klines("BTCUSDT", "1m"))
# print(cl.account())