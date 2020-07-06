from qtpylib.algo import Algo

class CrossOver(Algo):

    def on_start(self):
        pass

    def on_fill(self, instrument, order):
        pass

    def on_quote(self, instrument):
        pass

    def on_orderbook(self, instrument):
        pass

    def on_tick(self, instrument):
        pass

    def on_bar(self, instrument):
        # get instrument history
        bars = instrument.get_bars(window=100)

        # or get all instruments history
        # bars = self.bars[-20:]

        # skip first 20 days to get full windows
        if len(bars) < 20:
            return

        # compute averages using internal rolling_mean
        bars['short_ma'] = bars['close'].rolling_mean(window=10)
        bars['long_ma']  = bars['close'].rolling_mean(window=20)

        # get current position data
        positions = instrument.get_positions()

        # trading logic - entry signal
        if bars['short_ma'].crossed_above(bars['long_ma'])[-1]:
            if not instrument.pending_orders and positions["position"] == 0:

                # buy one contract
                instrument.buy(1)

                # record values for later analysis
                self.record(ma_cross=1)

        # trading logic - exit signal
        elif bars['short_ma'].crossed_below(bars['long_ma'])[-1]:
            if positions["position"] != 0:

                # exit / flatten position
                instrument.exit()

                # record values for later analysis
                self.record(ma_cross=-1)


if __name__ == "__main__":
    strategy = CrossOver(
        instruments = [ ("ES", "FUT", "GLOBEX", "USD", 202009, 0.0, "") ], # ib tuples
        resolution  = "1T", # Pandas resolution (use "K" for tick bars)
        tick_window = 20, # no. of ticks to keep
        bar_window  = 5, # no. of bars to keep
        preload     = "1D", # preload 1 day history when starting
        timezone    = "US/Central" # convert all ticks/bars to this timezone
    )
    strategy.run()