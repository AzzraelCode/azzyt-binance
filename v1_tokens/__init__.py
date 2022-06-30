import hashlib
import hmac
import requests

from time import time
timestamp = round(time() * 1000)

import creds
api_key = creds.api_key_testnet
sec_key = creds.sec_key_testnet

base_url = "https://testnet.binance.vision"

# https://binance-docs.github.io/apidocs/spot/en/#account-information-user_data
end_point = "/api/v3/account"

# https://binance-docs.github.io/apidocs/spot/en/#signed-trade-user_data-and-margin-endpoint-security
query = f"timestamp={timestamp}&recvWindow=50000"

# https://stackoverflow.com/a/53911060
signature = hmac.new(sec_key.encode(), query.encode(), hashlib.sha256).hexdigest()

r = requests.get(f"{base_url}{end_point}?{query}&signature={signature}", headers={'X-MBX-APIKEY': api_key})
print(r.status_code, r.headers)