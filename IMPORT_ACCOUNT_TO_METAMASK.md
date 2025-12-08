# How to Import Ganache Account to MetaMask

## Quick Steps:

1. **Open Ganache**
   - You should see your account: `0x494fbE29cbD884BAeB1366CE4Ad75A6A6e1Eb9e9`
   - Balance: 100.00 ETH

2. **Get the Private Key**
   - In Ganache, click the 🔑 (key) icon next to the account
   - OR click on the account row to see details
   - Copy the "Private Key" (it will be a long hex string starting with 0x)

3. **Add Ganache Network to MetaMask**
   - Open MetaMask extension
   - Click network dropdown (top center)
   - Click "Add Network" or "Add a network manually"
   - Fill in:
     ```
     Network Name: Ganache Local
     RPC URL: http://127.0.0.1:7545
     Chain ID: 1337
     Currency Symbol: ETH
     Block Explorer URL: (leave empty)
     ```
   - Click "Save"

4. **Switch to Ganache Network**
   - Select "Ganache Local" from network dropdown

5. **Import Account in MetaMask**
   - Click account icon (top right in MetaMask)
   - Click "Import Account"
   - Paste the private key you copied from Ganache
   - Click "Import"
   - You should now see 100 ETH!

## Network Details:
- **RPC URL**: http://127.0.0.1:7545
- **Chain ID**: 1337 (This is what MetaMask uses - Ganache's default)
- **Network ID**: 5777 (Internal Ganache network ID)
- **Currency**: ETH

**IMPORTANT**: Use Chain ID **1337** in MetaMask (not 5777). MetaMask checks the Chain ID and Ganache returns 1337.

## Troubleshooting:

- **No ETH showing?** Make sure you:
  - Are on the "Ganache Local" network (not Mainnet/Testnet)
  - Imported the correct account (the one with 100 ETH in Ganache)
  - Ganache is running on port 7545

- **Can't connect?** Check that:
  - Ganache is running and showing the account
  - The RPC URL is exactly: `http://127.0.0.1:7545`
  - Your firewall isn't blocking localhost connections

