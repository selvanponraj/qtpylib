#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# QTPyLib: Quantitative Trading Python Library
# https://github.com/ranaroussi/qtpylib
#
# Copyright 2016-2018 Ran Aroussi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import random

import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame

from qtpylib.algo import Algo
from qtpylib import futures


import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# from qtpylib import talib_indicators as ta
# from qtpylib import indicators as qtpylib


class ORBStrategy(Algo):
    """
    Example: This Strategy buys/sells single contract of the
    S&P E-mini Futures (ES) every 10th tick with a +/- 0.5
    tick target/stop using LIMIT order.

    If still in position for next 5 ticks, an exit order is issued.
    """

    count = 0

    # ---------------------------------------
    def on_start(self):
        """ initilize tick counter """
        self.count = 0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        """
        # Stoch

        stoch = ta.STOCH(dataframe)
        dataframe['slowk'] = stoch['slowk']

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # Inverse Fisher transform on RSI, values [-1.0, 1.0] (https://goo.gl/2JGGoy)
        rsi = 0.1 * (dataframe['rsi'] - 50)
        dataframe['fisher_rsi'] = (np.exp(2 * rsi) - 1) / (np.exp(2 * rsi) + 1)

        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']

        # SAR Parabol
        dataframe['sar'] = ta.SAR(dataframe)


        # Hammer: values [0, 100]
        dataframe['CDLHAMMER'] = ta.CDLHAMMER(dataframe)


        return dataframe


    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (dataframe['rsi'] < 30) &
                (dataframe['slowk'] < 20) &
                (dataframe['bb_lowerband'] > dataframe['close']) &
                (dataframe['CDLHAMMER'] == 100)
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (dataframe['sar'] > dataframe['close']) &
                (dataframe['fisher_rsi'] > 0.3)
            ),
            'sell'] = 1
        return dataframe

    # ---------------------------------------
    def on_quote(self, instrument):
        # quote = instrument.get_quote()
        # ^^ quote data available via get_quote()
        pass

    # ---------------------------------------
    def on_orderbook(self, instrument):
        pass

    # ---------------------------------------
    def on_fill(self, instrument, order):
        pass

    # ---------------------------------------
    def on_tick(self, instrument):
        # tick = instrument.get_tick()
        # # get OHLCV bars
        # print("TICK:", tick)
        pass

    # ---------------------------------------
    # def on_bar(self, instrument):
    #     # get instrument history
    #     bars = instrument.get_bars()
    #     # print(bars)
    #     # # make sure we have at least 20 bars to work with
    #     # if len(bars) < 20:
    #     #     return
    #
    #     indicators = self.populate_indicators(bars,None)
    #     bar = instrument.get_bars(lookback=1, as_dict=True)
    #
    #
    #     buy_signal = self.populate_buy_trend(indicators,None)
    #     if not np.isnan(buy_signal['buy'].iloc[-1]):
    #         # get OHLCV bars
    #         print('BUY::::::::::::')
    #         print("BAR:", bar)
    #         # send a buy signal
    #         instrument.buy(1)
    #         # record values for future analysis
    #         self.record(ma_buy=1)
    #
    #
    #     # sell_signal = self.populate_sell_trend(indicators,None)
    #     # if not np.isnan(buy_signal['sell'].iloc[-1]):
    #     #     print('SELL::::::::::::')
    #     #     print("BAR:", bar)
    #     #     # send a buy signal
    #     #     instrument.sell(1)
    #     #
    #     #     # record values for future analysis
    #     #     self.record(ma_sell=1)

    def on_bar(self, instrument):

        # Place Orders...
        bar = instrument.get_bars(lookback=1, as_dict=True)
        print("BAR:", bar)

        instrument_df = orb_results[orb_results['symbol'] == "IMB"]
        print(instrument_df)
        bar_close = bar['close']
        high = instrument_df['high'].values[0]
        low = instrument_df['low'].values[0]
        qty = instrument_df['qty'].values[0]

        direction ='NOT KNOWN'

        if bar['close'] > high:
            direction='BUY'
        if bar['close'] < low:
            direction='SELL'

        print(high, bar_close,low,direction)

        # get position direction
        if instrument.positions['position'] > 0 and direction =='BUY':
            # already buy order in place
            print('Already BUY order in Place - So not placing order - Position - ' + str(instrument.positions['position']))
            pass

        if instrument.positions['position'] < 0 and direction =='SELL':
            print('Already SELL order in Place - So not placing order - Position - ' + str(instrument.positions['position']))
            pass

        if not instrument.pending_orders and instrument.positions["position"] == 0:
            if direction =='BUY':
                print("BUY Signal and No Position - Placing Order")
                instrument.order(direction, qty, limit_price=high, initial_stop=high, stop_limit=True)
                self.record(ORB_BUY=qty)
            elif direction =='SELL':
                print("Sell Signal and No Position - Placing Order")
                instrument.order(direction, qty, limit_price=high, initial_stop=high, stop_limit=True)
                self.record(ORB_SELL=qty)
        elif instrument.positions['position'] > 0 and direction =='SELL':
            print('exiting BUY position - placing new SELL order - Position - ' + str(instrument.positions['position']))
            instrument.order(direction, qty, limit_price=high, initial_stop=high, stop_limit=True)
            self.record(ORB_SELL=qty)
        elif instrument.positions['position'] < 0 and direction =='BUY':
            print('exiting SELL position - placing new BUY order - Position - ' + str(instrument.positions['position']))
            instrument.order(direction, qty, limit_price=high, initial_stop=high, stop_limit=True)
            self.record(ORB_BUY=qty)

# ===========================================
if __name__ == "__main__":
    # # get most active ES contract to trade
    # ACTIVE_MONTH = futures.get_active_contract("ES")
    # print("Active month for ES is:", ACTIVE_MONTH)
    #
    # strategy = Strategy002(
    #     instruments=[("ES", "FUT", "GLOBEX", "USD", 202009, 0.0, "")],
    #     resolution="5T",
    #     ibport=7497
    # )
    #

    orb_results = pd.read_csv('~/auto_trade/ezibpy/scan_results/uk_orb_ib_result.csv')
    symbols = list(orb_results['symbol'])

    instruments = []
    for symbol in symbols:
        instruments.append( (symbol, "STK", "LSE", "GBP", "", 0.0, ""),)

    print(instruments)

    strategy = ORBStrategy(
        instruments=instruments,
        resolution="15T",
        ibport=7497
    )
    strategy.run()
