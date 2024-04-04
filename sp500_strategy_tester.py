import yfinance as yf
import pandas as pd # requests return pandas DataFrames, so it is useful to import pandas as well
import numpy as np
from enum import Enum, auto
import time

# Enumerate strategies
class StrategyNames(Enum):
    SMA_20_CROSSOVER_PRIORITY_ATR_SL5_TP10 = "SMA_20_CROSSOVER_PRIORITY_ATR_SL5_TP10"
    SMA_10_CROSSOVER_PRIORITY_ATR_SL5_TP10 = "SMA_10_CROSSOVER_PRIORITY_ATR_SL5_TP10",
    SMA_30_CROSSOVER_PRIORITY_ATR_SL5_TP10 = "SMA_30_CROSSOVER_PRIORITY_ATR_SL5_TP10",
    SMA_90_CROSSOVER_PRIORITY_ATR_SL5_TP10 = "SMA_90_CROSSOVER_PRIORITY_ATR_SL5_TP10"
    SMA_270_CROSSOVER_PRIORITY_ATR_SL5_TP10 = "SMA_270_CROSSOVER_PRIORITY_ATR_SL5_TP10"

'''---------------------------------------------------
--        CUSTOMIZE THIS PART (STRATEGIES)          --
----------------------------------------------------'''

SELECTED_STRATEGIES = [
    StrategyNames.SMA_10_CROSSOVER_PRIORITY_ATR_SL5_TP10,
    StrategyNames.SMA_30_CROSSOVER_PRIORITY_ATR_SL5_TP10,
    StrategyNames.SMA_90_CROSSOVER_PRIORITY_ATR_SL5_TP10,
    StrategyNames.SMA_270_CROSSOVER_PRIORITY_ATR_SL5_TP10
]

portfolio_equity = 10000

class Indicator:
    def __init__(self, min_indicator_length, calculate_value_func):
        self.min_indicator_length = min_indicator_length
        self.calculate_value_func = calculate_value_func


'''---------------------------------------------------
--               DEFINING FUNCTIONS                 --
----------------------------------------------------'''

# Defining Sma Indicator

def calculate_sma(price_df_slice):
    price_close_series = price_df_slice['Close']
    return price_close_series.mean()


sma_indicator = Indicator(2, calculate_sma)

def calculate_sma_crossover(price_df_slice):
    sma = calculate_sma(price_df_slice)
    second_most_recent_close = price_df_slice['Close'].iloc[-2]  # is < sma in crossover
    most_recent_close = df_slice['Close'].iloc[-1]  # is > sma in crossover

    return second_most_recent_close < sma < most_recent_close

sma_crossover_indicator = Indicator(3, calculate_sma_crossover)

def calculate_atr(price_df_slice):
    # Calculate the true ranges
    high_low = price_df_slice['High'] - price_df_slice['Low']
    high_close_prev = abs(price_df_slice['High'] - price_df_slice['Close'].shift(1))
    low_close_prev = abs(price_df_slice['Low'] - price_df_slice['Close'].shift(1))

    # Combine the true ranges into a single DataFrame and calculate max for each row
    true_ranges = pd.concat([high_low, high_close_prev, low_close_prev], axis=1).max(axis=1)

    # Calculate ATR by averaging the true ranges
    atr = true_ranges.mean()

    return atr


atr_indicator = Indicator(2, calculate_atr)

class Strategy:
    def __init__(self, indicator, signal_length, stop_loss_percentage, take_profit_percentage, enter_buy_trade_func):
        self.indicator = indicator
        self.signal_length = signal_length
        self.stop_loss_percentage = stop_loss_percentage
        self.take_profit_percentage = take_profit_percentage
        self.enter_buy_trade_func = enter_buy_trade_func # should take dict of

def sma_crossover_enter_buy_trade_func(dict_of_slices_of_each_stocks_df):
    trade_candidates = []

    for ticker_str, price_data_slice in dict_of_slices_of_each_stocks_df.items():
        if sma_crossover_indicator.calculate_value_func(price_data_slice):
            trade_candidates.append(ticker_str)

    if len(trade_candidates) == 0:
        return None
    if len(trade_candidates) == 1:
        return trade_candidates[0]

    # if made it here, more than one candidate, need to filter
    curr_best_candidate = trade_candidates[0]

    for candidate in trade_candidates:
        atr_curr_best_candidate = atr_indicator.calculate_value_func(dict_of_slices_of_each_stocks_df[curr_best_candidate])
        atr_curr_candidate = atr_indicator.calculate_value_func(dict_of_slices_of_each_stocks_df[candidate])
        if atr_curr_candidate > atr_curr_best_candidate:
            curr_best_candidate = candidate
    return curr_best_candidate


sma20_crossover_tp10_sl5_pref_h_atr_strategy = Strategy(sma_indicator, 21, 5, 10, sma_crossover_enter_buy_trade_func)
sma10_crossover_tp10_sl5_pref_h_atr_strategy = Strategy(sma_indicator, 11, 5, 10, sma_crossover_enter_buy_trade_func)
sma30_crossover_tp10_sl5_pref_h_atr_strategy = Strategy(sma_indicator, 31, 5, 10, sma_crossover_enter_buy_trade_func)
sma90_crossover_tp10_sl5_pref_h_atr_strategy = Strategy(sma_indicator, 91, 5, 10, sma_crossover_enter_buy_trade_func)
sma270_crossover_tp10_sl5_pref_h_atr_strategy = Strategy(sma_indicator, 271, 5, 10, sma_crossover_enter_buy_trade_func)

# DICT OF STRATEGIES

strategies = {
    StrategyNames.SMA_20_CROSSOVER_PRIORITY_ATR_SL5_TP10: sma20_crossover_tp10_sl5_pref_h_atr_strategy,
    StrategyNames.SMA_10_CROSSOVER_PRIORITY_ATR_SL5_TP10: sma10_crossover_tp10_sl5_pref_h_atr_strategy,
    StrategyNames.SMA_30_CROSSOVER_PRIORITY_ATR_SL5_TP10: sma30_crossover_tp10_sl5_pref_h_atr_strategy,
    StrategyNames.SMA_90_CROSSOVER_PRIORITY_ATR_SL5_TP10: sma90_crossover_tp10_sl5_pref_h_atr_strategy,
    StrategyNames.SMA_270_CROSSOVER_PRIORITY_ATR_SL5_TP10: sma270_crossover_tp10_sl5_pref_h_atr_strategy

}

'''---------------------------------------------------
--    LEAVE THIS PART (IT TESTS YOUR STRATEGY)       --
----------------------------------------------------'''

sp500_dfs = {}
saved_starting_equity = portfolio_equity

sp500_info_df = pd.read_csv('sp500-info.csv')

earliest_stock_data_date = pd.Timestamp.now(tz='America/New_York')
earliest_stock_ticker = 'no_ticker'

i = 1

# create dfs for all sp500 stocks, update Dates in dfs to pd Timestamp objects, store earliest day of data
for tuple in sp500_info_df.itertuples():
    index, ticker, name, GICS_sector, GICS_sub_industry, hq_location, date_added, cik, year_founded = tuple
    print(f'initializing df for ticker: {i} - {ticker}')
    i = i + 1
    curr_stock_df = pd.read_csv(f'sp500-10yr-hist-data/10yr-hist-{ticker}.csv')

    # update earliest_stock_data_date
    if len(curr_stock_df) != 0:
        sp500_dfs[ticker] = curr_stock_df

        # convert al dates in df to pd timestamps
        curr_stock_df['Date'] = pd.to_datetime(curr_stock_df['Date'], utc=True)
        curr_stock_df['Date'] = curr_stock_df['Date'].dt.tz_convert('America/New_York')

        earliest_date_curr_stock = curr_stock_df.iloc[0]['Date']
        if earliest_date_curr_stock < earliest_stock_data_date:
            earliest_stock_data_date = earliest_date_curr_stock
            earliest_stock_ticker = ticker


# get max length of all, this will be the trade starting date
date_to_start_trading = earliest_stock_data_date

def get_slice_of_length_signal_length(df, dates_so_far, signal_length):
    df_slice = df.iloc[dates_so_far - signal_length: dates_so_far]
    return df_slice



# Strategy Performance Collection
all_trading_dates = sp500_dfs[earliest_stock_ticker]['Date']

strategy_performance_dict = {
    'Date': all_trading_dates
}

strategy_performance_df = pd.DataFrame(strategy_performance_dict)

# Test each selected strategy by going through slices of indicator length for each sp500 stock and making trades
for SELECTED_STRATEGY in SELECTED_STRATEGIES:
    curr_strategy_portfolio_balances = []
    in_trade = False
    pnl = 0
    entry_price = 0
    trade_results = []
    curr_trade_ticker = ''
    trades_taken = 0
    portfolio_equity = 10000

    dates_so_far = 1
    for date in sp500_dfs[earliest_stock_ticker]['Date']:
        print(f" - - - - - - on date: {date}")
        if dates_so_far >= strategies[SELECTED_STRATEGY].signal_length:
            if in_trade:
                stock_bought_df = sp500_dfs[curr_trade_ticker]
                date_slice = stock_bought_df[stock_bought_df['Date'] == date]
                curr_price = date_slice['Close'].iloc[0]
                pnl = ((curr_price - entry_price) / entry_price) * 100

                if pnl <= strategies[SELECTED_STRATEGY].stop_loss_percentage or pnl >= strategies[SELECTED_STRATEGY].take_profit_percentage:
                    portfolio_equity = portfolio_equity * ((100 + pnl) / 100)
                    print(f"   Exit signal at date {date}. Close price: {curr_price:.2f}, PnL: {pnl:.2f}%. Equity: {portfolio_equity:.2f}")
                    # Assuming entire portfolio is used in trade at 1x leverage
                    in_trade = False
                    trade_results.append('Profit' if pnl > 0 else 'Loss')
            else:
                # make dict of slices for each stock
                dict_of_price_slices_all_available_stocks = {}

                for ticker, stock_df in sp500_dfs.items():
                    if not stock_df[stock_df['Date'] == date].empty:
                        # Get a slice of the dataframe whose size matches the indicator length
                        df_slice = get_slice_of_length_signal_length(stock_df, dates_so_far, strategies[SELECTED_STRATEGY].signal_length)
                        if len(df_slice) == strategies[SELECTED_STRATEGY].signal_length:
                           dict_of_price_slices_all_available_stocks[ticker] = df_slice

                # get stock to buy, if any
                ticker_to_buy = strategies[SELECTED_STRATEGY].enter_buy_trade_func(dict_of_price_slices_all_available_stocks)

                if ticker_to_buy and not in_trade:
                    in_trade = True  # Enter trade
                    stock_to_buy_df = sp500_dfs[ticker_to_buy]
                    date_slice = stock_to_buy_df[stock_to_buy_df['Date'] == date]
                    entry_price = date_slice['Close'].iloc[0]
                    trades_taken = trades_taken + 1
                    curr_trade_ticker = ticker_to_buy
                    print(f"Buy signal at date {date} for stock {curr_trade_ticker}. Close price: {entry_price:.2f}. Equity: {portfolio_equity:.2f}")
        dates_so_far += 1
        curr_strategy_portfolio_balances.append(portfolio_equity)


    print(f"\n* Starting Equity: ${saved_starting_equity}")
    print(f"* Final Equity: ${portfolio_equity:.2f}")
    print(f"* Total Return (Percentage): {((portfolio_equity / saved_starting_equity) * 100 - 100): .2f}%")
    print(f"* Trades Taken: {trades_taken}")

    strategy_performance_df[SELECTED_STRATEGY] = curr_strategy_portfolio_balances

strategy_performance_df.to_csv('sp500-sma-strategy-performance-data.csv', index=False)