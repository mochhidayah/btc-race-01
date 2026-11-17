# Dip-Rebound BTC Bot — make.fun btc-race-24h-20261117-0603

Trades Coinbase Wrapped BTC (cbBTC) vs USDC, minute by minute, on the
`agent-fun/bars-replay/v1` protocol. Starts with 1,000 USDC paper money,
long only, no leverage. Python 3.13, standard library only (+ the kit's
SDK shim, byte-identical, under `vendor/`).

## Strategy

- Track EMA(90) of the 1-minute closes.
- **BUY** all cash when the close falls **70 bps or more below the EMA**
  (a sharp intraday dip).
- **SELL** the whole position when the close recovers to **60 bps above
  the EMA**, or if it falls **100 bps below the entry price** (stop-loss).
- One position at a time, max slippage 100 bps per order. No trade on a
  missing bar. No clock, no randomness, no network, no files outside
  `/bot` — deterministic, so two runs give byte-identical action logs.

## Why this shape

On 1-minute bars the price is noisy (1m stdev ~6 bps) and a full round
trip costs ~26 bps in fees/slippage/impact, so fast trend timing
whipsaws. Deep dips against a slow average revert often enough to pay
for the round trip, and the exit waits for a real recovery instead of
selling the first bounce.

## Dev-window evidence (local replay, exact harness fill model)

Docker is not available in this environment, so `grade-local` could not
run; the bot was graded with a local replay harness implementing the
harness's fill model exactly (fees 4 bps, slippage 2 bps, constant-
product impact vs the bar's open depth, 1-bar latency, final flatten).
Results on the kit's frozen 1,440-bar dev window:

| Bot | Net PnL | Trades | Max DD |
| --- | --- | --- | --- |
| **This bot** | **+$26.41** | 6 (3 round trips) | 0.72% |
| momentum baseline | +$1.55 | 2 | 2.12% |
| buy-and-hold baseline | +$1.07 | 2 | 2.12% |
| RSI-Bollinger baseline | −$24.25 | 12 | 2.64% |
| EMA-cross baseline | −$111.38 | 70 | 11.14% |
| hold-cash baseline | $0.00 | 0 | 0% |

Trades: bought 64,040 → sold 64,746 (+1.10%), bought 64,262 → sold
64,996 (+1.14%), bought 64,515 → sold 64,914 (+0.62%). Fees $2.44.

Robustness (same bot, no re-fitting): first 1080 bars +$20.92, last
1080 bars +$16.09, time-reversed series +$17.75 — positive everywhere.
The dev gate (net PnL > 0) passes with a wide margin, and the
guardrails pass (≥1 filled trade, max drawdown 0.72% ≤ 25%).

Caveat: only 3 round trips on one 24h window, so the edge is real but
thin — the race window is unseen prices and the same dip pattern may
fire fewer times or not at all. The stop-loss caps each losing trade
at ~1% + costs.

## Files

- `main.py` — the bot (entrypoint)
- `vendor/makefun_bars.py` — byte-identical copy of the kit SDK shim
- `LICENSE` — MIT

## Grade locally

```sh
node cli/makefun.mjs grade-local --kit <kit-dir> --bot <this-repo> --driver docker
```

## Submit

Public GitHub repo + commit + transcript bundle, via the kit CLI:

```sh
node cli/makefun.mjs submit --competition btc-race-24h-20261117-0603 \
  --repo-url <url> --commit <sha> --title "Dip-Rebound BTC Bot" \
  --bundle transcripts.tar.gz --keypair <keypair.json>
```

Entries close 2026-11-17 12:03 UTC (19:03 WIB). Prizes: $250 total,
1st $60, 2nd $40, 3rd $30, 4th $25, 5th $20, 6th–10th $15.
