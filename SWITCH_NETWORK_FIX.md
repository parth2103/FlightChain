# Fix: Switch to Correct Ganache Network

## The Problem:
- MetaMask is connected to "Localhost 8545" 
- But Ganache is running on port **7545**
- Your account has 100 ETH on port 7545, but you're looking at port 8545 (which has 0 ETH)

## The Fix:

### Option 1: Switch to the Ganache Network You Already Added

1. **Click the network dropdown** in MetaMask (where it says "Localhost 8545")
2. **Select "Ganache Local"** (or whatever you named it when you added it with Chain ID 1337)
3. You should now see your 100 ETH!

### Option 2: If You Don't See "Ganache Local" in the List

You might have added the network but it's not showing. Let's add it again:

1. Click the network dropdown
2. Click "Add Network" or "Add a network manually"
3. Fill in:
   ```
   Network Name: Ganache Local
   RPC URL: http://127.0.0.1:7545
   Chain ID: 1337
   Currency Symbol: ETH
   Block Explorer URL: (leave empty)
   ```
4. Click "Save"
5. It should automatically switch to this network

## Verify Your Account:

The account with 100 ETH is:
- **Address**: `0x494fbE29cbD884BAeB1366CE4Ad75A6A6e1Eb9e9`
- **Network**: Must be connected to port 7545 (Chain ID 1337)

Make sure you imported THIS account in MetaMask!

## Quick Checklist:

✅ Ganache running on port 7545?  
✅ MetaMask connected to network with RPC URL `http://127.0.0.1:7545`?  
✅ Chain ID is 1337?  
✅ Imported account `0x494fbE29cbD884BAeB1366CE4Ad75A6A6e1Eb9e9`?  
✅ Selected that imported account in MetaMask?

If all checked, you should see 100 ETH!

