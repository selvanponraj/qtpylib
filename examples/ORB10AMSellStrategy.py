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

import pandas as pd  # noqa
from qtpylib.algo import Algo


class ORB10AMSellStrategy(Algo):
    count = 0

    # ---------------------------------------
    def on_start(self):
        """ initilize tick counter """
        self.count = 0

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
        pass

    def on_bar(self, instrument):
        # Place Orders...
        bar = instrument.get_bars(lookback=1, as_dict=True)
        instrument_df = orb_results[orb_results['symbol'] == instrument.symbol]
        bars = instrument.get_bars(lookback=3)
        print(bars)
        bars_total_volume = bars['volume'].sum()
        avg_volume = round(bars_total_volume / 3)
        print(avg_volume)
        bar_close = bar['close']
        high = instrument_df['high'].values[0]
        low = instrument_df['low'].values[0]
        qty = instrument_df['qty'].values[0]
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
                                 target=high + (high * .01),
                                 expiry=240)

                self.record(ORB_BUY=qty)
            elif direction == 'SELL':
                print("Sell Signal and No Position - Placing Order")
                print(instrument.symbol, high, bar_close, low, direction, volume, avg_volume)
                instrument.order(direction,
                                 qty,
                                 limit_price=low,
                                 initial_stop=high,
                                 trail_stop_by=0.5,
                                 target=low - (low * .01),
                                 expiry=240)
                self.record(ORB_SELL=qty)


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

    scan_result = market + '_10am-sell_ib_result.csv'
    orb_results = pd.read_csv('~/auto_trade/ezibpy/scan_results/' + scan_result)
    symbols = list(orb_results['symbol'])

    instruments = []
    for symbol in symbols:
        if market=='uk':
            instruments.append((symbol, "STK", "LSE", "GBP", "", 0.0, ""))
        elif market=='us':
            instruments.append((symbol, "STK", "SMART", "USD", "", 0.0, ""))
    print('Instruments:',instruments)

    strategy = ORB10AMSellStrategy(
            instruments=instruments,
            resolution="15T",
            ibport=7497,
            ibclient=803
        )
    strategy.run()