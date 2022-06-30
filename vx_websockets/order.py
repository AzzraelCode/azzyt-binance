import click
import creds
from vx_websockets import get_spot_client

click.secho("Отправка Заявки", fg="red")

client = get_spot_client()

r = client.depth(symbol=creds.symbol, limit=1)
best_buy = r.get('bids')[-1][0]
print(best_buy)

r = client.new_order(
    symbol=creds.symbol,
    quantity=0.001,
    side='BUY',
    type="LIMIT",
    price=best_buy,
    timeInForce="GTC"
)

print(r)

# r = client.cancel_open_orders(creds.symbol)
# print(r)