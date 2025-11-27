# Token Efficiency Proof

Mathematical derivation of O(n²) vs O(n) scaling.

## Assumptions

```
SYSTEM  = 1500 tokens   # Tool schemas + protocol + memory
THINK   = 200 tokens    # Agent reasoning
CALLS   = 100 tokens    # Tool invocation JSON
RESULTS = 300 tokens    # Tool output
```

## Replay (HTTP)

Each turn replays growing history:

```
Turn 1: SYSTEM + THINK + CALLS = 1800
Turn 2: SYSTEM + [Turn 1] + RESULTS + THINK + CALLS = 2400
Turn n: 1800 + 600(n-1)
```

**Total for n turns:**
```
Σ[1800 + 600(k-1)] for k=1 to n
= 1800n + 600 × n(n-1)/2
= 1500n + 300n²
```

## Resume (WebSocket)

Server maintains state, only incremental content:

```
Turn 1: SYSTEM + THINK + CALLS = 1800
Turn 2: RESULTS + THINK + CALLS = 600
Turn n: 600
```

**Total for n turns:** `1200 + 600n`

## Comparison

| Turns | Replay | Resume | Ratio |
|-------|--------|--------|-------|
| 1 | 1,800 | 1,800 | 1.0x |
| 8 | 31,200 | 6,000 | 5.2x |
| 16 | 100,800 | 10,800 | 9.3x |
| 32 | 355,200 | 20,400 | 17.4x |

**Efficiency ratio:** `(1500n + 300n²) / (1200 + 600n)`

**Limit as n → ∞:** `n/2`

The efficiency advantage grows linearly with conversation depth.
