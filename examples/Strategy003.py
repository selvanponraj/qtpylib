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
import numpy
import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame

from qtpylib.algo import Algo
from qtpylib import futures


import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy

# from qtpylib import talib_indicators as ta
#
# from qtpylib import indicators as qtpylib


class Strategy003(Algo):
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

        # MFI
        dataframe['mfi'] = ta.MFI(dataframe)

        # Stoch fast
        stoch_fast = ta.STOCHF(dataframe)
        dataframe['fastd'] = stoch_fast['fastd']
        dataframe['fastk'] = stoch_fast['fastk']

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # Inverse Fisher transform on RSI, values [-1.0, 1.0] (https://goo.gl/2JGGoy)
        rsi = 0.1 * (dataframe['rsi'] - 50)
        dataframe['fisher_rsi'] = (numpy.exp(2 * rsi) - 1) / (numpy.exp(2 * rsi) + 1)

        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']

        # EMA - Exponential Moving Average
        dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
        dataframe['ema10'] = ta.EMA(dataframe, timeperiod=10)
        dataframe['ema50'] = ta.EMA(dataframe, timeperiod=50)
        dataframe['ema100'] = ta.EMA(dataframe, timeperiod=100)

        # SAR Parabol
        dataframe['sar'] = ta.SAR(dataframe)

        # SMA - Simple Moving Average
        dataframe['sma'] = ta.SMA(dataframe, timeperiod=40)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                    (dataframe['rsi'] < 28) &
                    (dataframe['rsi'] > 0) &
                    (dataframe['close'] < dataframe['sma']) &
                    (dataframe['fisher_rsi'] < -0.94) &
                    (dataframe['mfi'] < 16.0) &
                    (
                            (dataframe['ema50'] > dataframe['ema100']) |
                            (qtpylib.crossed_above(dataframe['ema5'], dataframe['ema10']))
                    ) &
                    (dataframe['fastd'] > dataframe['fastk']) &
                    (dataframe['fastd'] > 0)
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
        # get OHLCV bars
        # print("TICK:", tick)
        pass

    # ---------------------------------------
    def on_bar(self, instrument):
        # nothing exiting here...
        bars = instrument.get_bars()
        indicators = self.populate_indicators(bars,None)
        buy_signal = self.populate_buy_trend(indicators,None)
        sell_signal = self.populate_sell_trend(indicators,None)

        print("Buy Signal :")
        print(buy_signal)
        print("Sell Signal :")
        print(sell_signal)
        # Place Order
        bar = instrument.get_bars(lookback=1, as_dict=True)
        # get OHLCV bars
        print("BAR:", bar)

# ===========================================
if __name__ == "__main__":
    # get most active ES contract to trade
    ACTIVE_MONTH = futures.get_active_contract("ES")
    print("Active month for ES is:", ACTIVE_MONTH)

    strategy = Strategy003(
        instruments=[("ES", "FUT", "GLOBEX", "USD", 202009, 0.0, "")],
        resolution="1T",
        tick_window=10,
        bar_window=10,
        ibport=7497
    )
    strategy.run()
