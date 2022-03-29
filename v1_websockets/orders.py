import click
import creds
import pandas as pd

from . import get_spot_client

click.secho("Список ордеров", fg="blue")

client = get_spot_client()

print(pd.DataFrame(client.account().get('balances')))

df = pd.DataFrame(
    client.get_orders(symbol=creds.symbol),
    columns=['orderId', 'type', 'side', 'price', 'status']
)

print(df.tail(15))