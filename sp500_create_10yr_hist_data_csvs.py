import yfinance as yf
import pandas as pd # requests return pandas DataFrames, so it is useful to import pandas as well
import time

# read into list the sp500-tickers-and-names
sp500_info_df = pd.read_csv('sp500-info.csv')
sp500_info_df['dates_added'] = pd.to_datetime(sp500_info_df['dates_added'])

on_ticker = 1

for tuple in sp500_info_df.itertuples(index=False):
    ticker, name, GICS_sector, GICS_sub_industry, hq_location, date_added, cik, yr_founded = tuple

    print(f"On ticker {on_ticker} - {ticker}")

    ticker_obj = yf.Ticker(ticker)
    ticker_hist = ticker_obj.history(period="120mo")
    ticker_hist.to_csv(f'sp500-10yr-hist-data/10yr-hist-{ticker}.csv')

    on_ticker = on_ticker + 1
    time.sleep(2)