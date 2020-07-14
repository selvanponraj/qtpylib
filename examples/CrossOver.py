import sys

from qtpylib.algo import Algo


class CrossOver(Algo):

    def on_bar(self, instrument):
        numBars = 3
        # get instrument history
        bars = instrument.get_bars(lookback=numBars)
        print(bars)
        print("on_bar called with %i bars for symbol %s" % (len(bars), instrument.symbol))
        # make sure we have at least 20 bars to work with
        if len(bars) < numBars:
            return

        print("Hooray!  We finally have at least %i bars" % numBars)

        sys.exit()


if __name__ == "__main__":
    strategy = CrossOver(
        instruments=[('IBDE30','CFD','SMART','EUR')],
        resolution="1T",
        preload = "5T",
        ibport=7497
    )

    strategy.run()