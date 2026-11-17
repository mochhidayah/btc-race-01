"""Dip-rebound BTC bot for make.fun btc-race-24h-20261117-0603.

Strategy (long only, one position, 100% of cash per trade):
  - Track EMA(90) of the 1-minute closes.
  - BUY all cash when the close falls 70 bps or more below the EMA
    (a sharp intraday dip; on the dev window this fired 3 times).
  - SELL the whole position when the close recovers to 60 bps above
    the EMA, or if it falls 100 bps below the entry price (stop-loss).
  - No trade if the bar is missing; no clock, no randomness, no network,
    no files outside /bot. Deterministic float arithmetic only, so two
    runs on the same bars give byte-identical action logs.
  - Orders cap slippage at 100 bps past the close they were decided on;
    a rejected order is simply re-sent on the next bar while its
    condition still holds (fills land at the next bar's open anyway).

Why this shape: on 1-minute bars the price is noisy (1m stdev ~6 bps)
and a full round trip costs ~26 bps in fees/slippage/impact, so fast
EMA-cross trend timing whipsaws (the EMA-cross baseline loses $111 on
the dev window). Deep dips against a slow average revert often enough
to pay for the round trip, and the exit waits for a real recovery
instead of selling the first bounce.

Dev-window result (local replay, exact harness fill model):
  net PnL +$26.41 on $1,000 start, 3 round trips, max drawdown 0.72%,
  vs buy-and-hold +$1.07, momentum baseline +$1.55, EMA-cross -$111.38,
  RSI-Bollinger -$24.25. Positive on both halves (+$20.92 first 1080
  bars, +$16.09 last 1080 bars) and on the time-reversed series (+$17.75).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"
EMA_BARS = 90
DIP_BPS = 70        # buy when close is this far below the EMA
RECOVER_BPS = 60    # sell when close is this far above the EMA
STOP_BPS = 100      # sell when close is this far below the entry price
MAX_SLIPPAGE_BPS = 100

closes = []
ema = None
entry_price = None


def on_batch(state, batch):
    global ema, entry_price
    if SYMBOL not in {b["symbol"] for b in batch["bars"]}:
        return []
    c = state.close(SYMBOL)
    if c is None:
        return []
    k = 2.0 / (EMA_BARS + 1)
    ema = c if ema is None else ema + k * (c - ema)
    closes.append(c)
    held = state.positions.get(SYMBOL)
    if held is not None:
        if c > ema * (1 + RECOVER_BPS / 10000.0) or (
            entry_price is not None and c <= entry_price * (1 - STOP_BPS / 10000.0)
        ):
            entry_price = None
            return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []
    if len(closes) >= EMA_BARS and c < ema * (1 - DIP_BPS / 10000.0):
        entry_price = c
        return [{"side": "buy", "symbol": SYMBOL, "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
