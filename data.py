import pandas as pd
import numpy as np
import datetime as dt
from yahoo_finance import Share
from fredapi import Fred


class Data:
    def __init__(self):
        pass

    def stock_dao(self, stocks=[]):
        data = pd.DataFrame()
        dates=[]
        for stock in stocks:
            s = Share(stock)
            d = pd.DataFrame(s.get_historical('2007-01-01', '2016-06-01'))
            print(d)
            dates = d['Date']
            x = d['Adj_Close']
            x = x.astype(float)
            data[stock] = x.pct_change(periods=1)
        data['Dates'] = dates
        return data

    def macoeconomic_shock_dao(self, shock):
        fred = Fred(api_key='2d4b5ef2420e64d7e42928ffd9d6ff8c')
        d = pd.DataFrame(fred.get_series_as_of_date(shock, '6/1/2016'))
        data = pd.DataFrame()
        data['Dates'] = d['realtime_start']
        x = d['value']
        data[shock] = x.pct_change(periods=1)
        data = data.sort_values('Dates')
        data = data.drop_duplicates(subset='Dates')
        return data

    def prepocess_stock_data(self, stocks=[]):
        stock_data = self.stock_dao(stocks=stocks)
        stock_data.Dates = pd.to_datetime(stock_data['Dates'], format='%Y-%m-%d')
        stock_data.set_index(['Dates'], inplace=True)

        # calculate percent change
        stock_data = stock_data.pct_change(periods=1)
        stock_data.to_csv(path_or_buf='stocks.csv', sep=',')
        return stock_data

    def preprocess_macroeconomic_data(self):
        gdp = self.macoeconomic_shock_dao(shock='GDP')
        umcsent = self.macoeconomic_shock_dao(shock='UMCSENT')
        cpi = self.macoeconomic_shock_dao(shock='CPIAUCSL')

        shock_data = pd.merge(gdp, umcsent, how='outer', on='Dates')
        shock_data = shock_data.sort_values('Dates')
        shock_data = pd.merge(shock_data, cpi, how='outer', on='Dates')
        shock_data = shock_data.sort_values('Dates')

        shock_data.dates = pd.to_datetime(shock_data['Dates'], format='%Y-%m-%d')
        shock_data.set_index(['Dates'], inplace=True)

        shock_data = shock_data.fillna(0)
        shock_data['GDP'] = shock_data['GDP'].astype(float)
        shock_data['UMCSENT'] = shock_data['UMCSENT'].astype(float)
        shock_data['CPIAUCSL'] = shock_data['CPIAUCSL'].astype(float)

        start = shock_data.index.searchsorted(dt.datetime(2007, 1, 1))
        end = shock_data.index.searchsorted(dt.datetime(2016, 6, 1))
        shock_data = shock_data[start:end]
        shock_data.to_csv(path_or_buf='shocks.csv', sep=',')
        return shock_data

    def get_seasonality_effects(self, data):
        df = pd.to_datetime(data, format='%Y-%m-%d')

        monday = [1 if x.weekday() == 0 else 0 for x in df]
        january = [1 if x.month == 1 else 0 for x in df]
        end = [1 if x.month == 12 else 0 for x in df]

        matrix = np.column_stack((monday, january, end))
        return matrix