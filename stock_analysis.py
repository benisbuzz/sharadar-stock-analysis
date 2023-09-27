import nasdaqdatalink as nq
from matplotlib import pyplot as plt
import mplfinance as mpf
import pandas as pd
from typing import Literal, Optional
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
import math
import random
import os
from dotenv import load_dotenv
load_dotenv()

nq.ApiConfig.api_key= os.getenv("NASDAQ_DATA_LINK_API_KEY")

class StockAnalysis:
    def __init__(self, ticker: str, lookback_years: Optional[int] = 10) -> None:
        self.ticker = ticker.upper()
        start_date = (dt.today() - relativedelta(years=lookback_years)).strftime("%Y-%m-%d")

        self.price_data = self.__get_data("SEP", date = {"gte": start_date}).set_index("date").sort_index()
        sf1 = self.__get_data("SF1", calendardate = {"gte": start_date}, dimension = "ARQ").set_index("calendardate")
        tickers = self.__get_data("TICKERS").iloc[[0]]

        self.__save_attributes(sf1, tickers)
        
    def __load_data(self, table_name: Literal["SF1", "SEP", "TICKERS"], **kwargs) -> pd.DataFrame:
        ticker = self.ticker
        return nq.get_table(
            f"SHARADAR/{table_name}",
            ticker = ticker,
            paginate = True,
            **kwargs)
    
    def __get_data(self, table_name: Literal["SF1", "SEP", "TICKERS"], **kwargs):
        data = self.__load_data(table_name, **kwargs)
        if len(data) == 0:
            if table_name == "SF1":
                print("No quarterly data: fetching yearly")
                data = self.__load_data(table_name,
                                        **{key : value for key, value in kwargs.items() if key != "dimension"},
                                        dimension = "ARY")
            else:
                print(f"No data for {table_name}")
        return data
    
    def __save_attributes(self, *args: pd.DataFrame) -> None:
        for arg in args:
            for column in arg.columns:
                setattr(self, column, arg[column].sort_index())

    @property  
    def chart(self):
        price_data = self.price_data
        self.weekly_price_data = price_data.resample(
            "W"
            ).agg({'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'})
        mpf.plot(self.weekly_price_data, type='candle',
                style='yahoo', ylabel='Price', ylabel_lower='Volume', 
                volume=True, figratio=(16, 8), tight_layout=True,
                mav=(15, 52))
    
    def plot_attributes(self, **kwargs) -> None:
        color_list = ['b','g','r','c','m','y']
        used_colors = []
        plot_dimensions = kwargs.get("plot_dimensions", (1,1))

        fig, ax = plt.subplots(
            nrows= plot_dimensions[0], 
            ncols= plot_dimensions[1],
            figsize = (20,10))
        
        # def plot_data(data, ax, coords, used_colors):
        #     color_list = ['b','g','r','c','m','y']
        #     available_colors = list(set(color_list).symmetric_difference(set(used_colors)))
        #     color = random.choice(available_colors)
        #     if coords:
        #         ax[coords].plot(data, label)


        if plot_dimensions == (1,1):
            for key, value in kwargs.items():
                available_colors = list(set(color_list).symmetric_difference(set(used_colors)))
                color = random.choice(available_colors)
                ax.plot(value, label = key.upper(), color = color)
                ax.yaxis.grid(color='gray', linestyle='dashed')
                ax.legend(loc = "upper left")
                used_colors.append(color)

        else:
            number_of_plots = math.prod(plot_dimensions)
            if len([key for key in kwargs.keys() if key != "plot_dimensions"]) != number_of_plots:
                raise ValueError("Number of datapoints does not equal number of plots")
            if 1 in plot_dimensions:
                all_coordinates = [i for i in range(number_of_plots)]
            else:
                all_coordinates = [(i, j) for i in range(plot_dimensions[0]) for j in range(plot_dimensions[1])]
            for data, coordinate in zip(kwargs.items(), all_coordinates):
                available_colors = list(set(color_list).symmetric_difference(set(used_colors)))
                color = random.choice(available_colors)
                ax[coordinate].plot(data[1], label = data[0].upper(), color = color)
                ax[coordinate].yaxis.grid(color='gray', linestyle='dashed')
                ax[coordinate].legend(loc = "upper left")
                used_colors.append(color)
    
    @property
    def multiples(self):
        multiples = {
            "PE" : self.pe, 
            "PS" : self.ps, 
            "PB" : self.pb, 
            "EV/EBITDA" : self.ev / self.ebitda, 
            "DEBT/EQUITY" : self.debt / self.equity, 
            "ROE" : self.equity.pct_change(),
            "DIVIDEND YIELD" : self.divyield
        }
        for key, value in multiples.items():
            print(f"{key} : {value.iloc[-1]}")
        
    @property
    def summary(self):
        self.plot_attributes(
            bvps = self.bvps,
            eps = self.eps,
            ncfo = self.ncfo / self.sharesbas,
            ebitda = self.ebitda,
            ev_ebitda = self.evebitda,
            debt_equity = self.debt / self.equity,
            plot_dimensions = (2,3)
        )

    @property
    def balance_sheet(self):
        balance_sheet_items = {
            "Cash and Cash Equiv"
        }

        





    





