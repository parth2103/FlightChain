# FlightChain

**Blockchain-Verified Flight Event Tracking System**

flightChain is a full-stack web application that provides transparent, verifiable flight event data. It leverages Ethereum smart contracts to immutable record flight events, ensuring data integrity for passengers, insurers, and aviation stakeholders.

## 🚀 Features

- **Flight Search**: Real-time flight tracking by flight number (e.g., UA123).
- **Event Timeline**: Detailed timeline of flight events (Gates, Takeoff, Landing).
- **Blockchain Verification**: Every event is hashed and stored on a local Ethereum blockchain (Ganache), with visual verification badges.
- **Delay Analysis**: Automated analysis of delay reasons using event timestamps.
- **Historical Baseline**: Route performance comparison.
- **Aircraft Metadata**: Detailed aircraft information.

## 🏗 Architecture

- **Frontend**: Next.js 14, Ant Design, TypeScript
- **Backend**: FastAPI, SQLAlchemy, Web3.py
- **Database**: MySQL
- **Blockchain**: Truffle, Ganache (Local Ethereum), Solidity

## 🛠 Prerequisites

- Node.js 18+
- Python 3.10+
- MySQL 8.0+
- Ganache (CLI or GUI)

## 🏁 Getting Started

### 1. Blockchain Setup

Start local blockchain and deploy contracts.

```bash
# Terminal 1
cd blockchain
npm install
npm run ganache  # Starts Ganache on port 8545
```

```bash
# Terminal 2 - Deploy Contract
cd blockchain
truffle migrate --network development
# Copy the deployed Contract Address!
```

### 2. Backend Setup

Configure and start the Python API.

```bash
# Terminal 3
cd backend

# create .env file
echo "DATABASE_URL=mysql+pymysql://root:password@localhost:3306/flightchain" > .env
echo "GANACHE_URL=http://127.0.0.1:8545" >> .env
echo "CONTRACT_ADDRESS=YOUR_CONTRACT_ADDRESS_HERE" >> .env  # Paste address from step 1

# Install dependencies
pip install -r requirements.txt

# Init DB (Make sure MySQL is running and database 'flightchain' exists)
mysql -u root -p -e "CREATE DATABASE flightchain;"
mysql -u root -p flightchain < migrations/schema.sql

# Start Server
uvicorn main:app --reload
```

### 3. Frontend Setup

Start the Next.js application.

```bash
# Terminal 4
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` to start FlightChain!

## 🧪 Testing

- **Backend Tests**: `pytest`
- **Smart Contract Tests**: `truffle test`

## 📝 License

MIT
