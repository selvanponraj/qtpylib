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
from datetime import timedelta
import datetime
from pytz import timezone

import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib


# from qtpylib import talib_indicators as ta
# from qtpylib import indicators as qtpylib


class TestStrategy(Algo):
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
        bar = instrument.get_bar()
        print("BAR:", bar)

        # bars = instrument.get_bars(lookback=100)
        bars = strategy.get_history(instrument.symbol, bar_start_time, resolution=resolution)
        print('full bars:')
        print(bars)
        bars_total_volume = bars['volume'].sum()
        if len(bars) > 0:
            avg_volume = round(bars_total_volume / len(bars))
        else:
            avg_volume = bars_total_volume

        # orb_bars = bars.session(start='19:31', end='19:35')
        orb_bars = bars[bars.index >= bar_start_time]
        orb_bars = bars[bars.index < bar_end_time]

        print("orb_bars:")
        print(orb_bars[['symbol', 'high', 'low', 'volume']])

        if len(orb_bars) >= 4:
            open_candle = orb_bars.iloc[0]
            second_candle = orb_bars.iloc[1]
            third_candle = orb_bars.iloc[2]
            fourth_candle = orb_bars.iloc[3]

            if ((second_candle.high < open_candle.high and second_candle.low > open_candle.low) and
                    (third_candle.high < open_candle.high and third_candle.low > open_candle.low) and
                    (fourth_candle.high < open_candle.high and fourth_candle.low > open_candle.low)):

                print("ORD Condition Matched")

                print(orb_bars)

                high = round(open_candle.high, 2)
                low = round(open_candle.low, 2)
                qty = int(10000 / ((high + low) / 2))
                volume = bar['volume']
                bar_close = bar['close']
                bar_close = bar['close']
                volume = bar['volume']

                direction = 'NOT KNOWN'
                if bar['close'] > high and volume > avg_volume:
                    direction = 'BUY'
                if bar['close'] < low and volume > avg_volume:
                    direction = 'SELL'

                # get position direction
                if instrument.positions['position'] > 0 and direction == 'BUY':
                    # already buy order in place
                    print('Already BUY order in Place - So not placing order - Symbol :', instrument.symbol, 'Position: ',
                          str(instrument.positions['position']))
                    pass

                if instrument.positions['position'] < 0 and direction == 'SELL':
                    print('Already SELL order in Place - So not placing order - Symbol :', instrument.symbol, 'Position: ',
                          str(instrument.positions['position']))
                    pass

                if not instrument.pending_orders and instrument.positions["position"] == 0:
                    if direction == 'BUY':
                        print("BUY Signal and No Position - Placing Order")
                        print(instrument.symbol, high, bar_close, low, direction, volume, avg_volume)
                        instrument.order(direction,
                                         qty,
                                         limit_price=high,
                                         initial_stop=low,
                                         trail_stop_by=0.5,
                                         target=high + (high - low),
                                         expiry=14400)

                        self.record(ORB_BUY=qty)
                    elif direction == 'SELL':
                        print("Sell Signal and No Position - Placing Order")
                        print(instrument.symbol, high, bar_close, low, direction, volume, avg_volume)
                        instrument.order(direction,
                                         qty,
                                         limit_price=low,
                                         initial_stop=high,
                                         trail_stop_by=0.5,
                                         target=low - (high - low),
                                         expiry=14400)
                        self.record(ORB_SELL=qty)

        # elif instrument.positions['position'] > 0 and direction =='SELL':
        #     print('exiting BUY position - placing new SELL order - Position - ' + str(instrument.positions['position']))
        #     print(instrument.symbol, high, bar_close, low, direction)
        #     instrument.order(direction, qty)
        #     self.record(ORB_SELL=qty)
        # elif instrument.positions['position'] < 0 and direction =='BUY':
        #     print('exiting SELL position - placing new BUY order - Position - ' + str(instrument.positions['position']))
        #     print(instrument.symbol, high, bar_close, low, direction)
        #     instrument.order(direction, qty)
        #     self.record(ORB_BUY=qty)


# ===========================================
if __name__ == "__main__":
    mk_list = ['uk', 'us']
    print("Available Markets:")
    for i, market in enumerate(mk_list, start=1):
        print('{}. {}'.format(i, market))

    while True:
        try:
            selected = int(input('Select a market (1-{}): '.format(i)))
            market = mk_list[selected - 1]
            print('You have selected {}'.format(market))
            break
        except (ValueError, IndexError):
            print('This is not a valid selection. Please enter number between 1 and {}!'.format(i))

    if market == 'uk':
        file_name = 'ftse.csv'
    elif market == 'us':
        file_name = 'sp100.csv'

    source = pd.read_csv(file_name, header=None).head(100)
    symbols = list(source.iloc[:,0])

    bar_time_format = '%Y-%m-%d %H:%M:%S'
    algo_time = timezone('UTC').localize(datetime.datetime.today() - timedelta(days=0))
    instruments = []
    for symbol in symbols:
        if market == 'uk':
            instruments.append((symbol, "STK", "LSE", "GBP", "", 0.0, ""))
            bar_start_time = algo_time.replace(hour=8).replace(minute=00).replace(second=00).strftime(
                bar_time_format)
            bar_end_time = algo_time.replace(hour=9).replace(minute=00).replace(second=00).strftime(
                bar_time_format)
        elif market == 'us':
            instruments.append((symbol, "STK", "SMART", "USD", "", 0.0, ""))
            bar_start_time = algo_time.replace(hour=19).replace(minute=31).replace(second=00).strftime(
                bar_time_format)
            bar_end_time = algo_time.replace(hour=19).replace(minute=35).replace(second=00).strftime(
                bar_time_format)
    print(instruments)
    resolution = '1T'
    strategy = TestStrategy(
        instruments=['AAPL'],
        resolution=resolution,
        preload="5T",
        ibport=7497,
        ibclient=2555,
        timezone='BST'
    )

    # bars = strategy.get_history('AAPL', bar_start_time, resolution=resolution)
    # print('full bars:')
    # print(bars)
    #
    # # orb_bars = bars.session(start='19:31', end='19:35')
    # orb_bars = bars[bars.index >= bar_start_time]
    # orb_bars = bars[bars.index < bar_end_time]
    #
    # print(orb_bars[['symbol','high','low','volume']])
    # bars = strategy.get_history('AAPL', bar_start_time, resolution=resolution)
    #
    # print (bars)
    # print(bar_end_time)
    # bars = bars[bars.index >= bar_start_time]
    # bars = bars[bars.index < bar_end_time]
    # print(bars)

    # strategy.get_instrument()
    strategy.run()