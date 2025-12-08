# Fix MetaMask Chain ID Error

## The Problem:
MetaMask says: "The RPC URL you have entered returned a different chain ID (1337)"

This means Ganache is using Chain ID **1337**, but you entered **5777**.

## The Fix:

1. **In the MetaMask form, change:**
   - Chain ID: Change from `5777` to `1337`

2. **Also make sure your RPC URL includes `http://`:**
   - RPC URL: `http://127.0.0.1:7545` (not just `127.0.0.1:7545`)

## Correct Settings:

```
Network Name: Ganache Local
RPC URL: http://127.0.0.1:7545
Chain ID: 1337  ← CHANGE THIS FROM 5777 TO 1337
Currency Symbol: ETH
Block Explorer URL: (leave empty)
```

After changing Chain ID to **1337**, the error will disappear and you can click "Save"!

## Why the confusion?
- Ganache shows "Network ID: 5777" in its interface
- But the actual **Chain ID** (what MetaMask checks) is **1337**
- MetaMask uses Chain ID, not Network ID

