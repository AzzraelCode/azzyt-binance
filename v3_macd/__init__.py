from binance.spot import Spot
import pandas as pd
from pandas import DataFrame

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

if __name__ == '__main__':
    cl = Spot()
    r = cl.klines("BTCUSDT", "1h", limit=300)
    df = DataFrame(r).iloc[:, :5]
    df.columns = list("tohlc")
    df['ma_fast'] = df['c'].ewm(span=12, adjust=False).mean()
    df['ma_slow'] = df['c'].ewm(span=26, adjust=False).mean()
    df['macd'] = df['ma_fast'] - df['ma_slow']
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    print(df.tail(10))