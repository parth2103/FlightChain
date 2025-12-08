/**
 * Web3 Service - MetaMask Integration
 * 
 * Handles blockchain interactions via MetaMask wallet.
 * Users sign and pay for their own transactions.
 */

import { ethers } from 'ethers';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Contract ABI - must match FlightEventRegistry.sol
export const CONTRACT_ABI = [
    "function recordEvent(string memory _flightId, string memory _eventType, uint256 _timestamp, string memory _actor, bytes32 _dataHash) external returns (uint256)",
    "function getFlightEventIndices(string memory _flightId) external view returns (uint256[])",
    "function getEvent(uint256 _index) external view returns (string memory flightId, string memory eventType, uint256 timestamp, string memory actor, bytes32 dataHash, uint256 blockNumber, uint256 recordedAt)",
    "function getTotalEvents() external view returns (uint256)",
    "function verifyHash(bytes32 _dataHash) external view returns (bool)"
];

/**
 * Check if MetaMask is installed
 */
export function isMetaMaskInstalled(): boolean {
    return typeof window !== 'undefined' && typeof (window as any).ethereum !== 'undefined';
}

/**
 * Request account access from MetaMask
 */
export async function connectMetaMask(): Promise<string> {
    if (!isMetaMaskInstalled()) {
        throw new Error('MetaMask is not installed. Please install MetaMask to continue.');
    }

    const provider = new ethers.BrowserProvider((window as any).ethereum);
    const accounts = await provider.send('eth_requestAccounts', []);
    
    if (accounts.length === 0) {
        throw new Error('No accounts found. Please unlock MetaMask.');
    }

    return accounts[0];
}

/**
 * Get the current connected account
 */
export async function getCurrentAccount(): Promise<string | null> {
    if (!isMetaMaskInstalled()) {
        return null;
    }

    try {
        const provider = new ethers.BrowserProvider((window as any).ethereum);
        const accounts = await provider.listAccounts();
        return accounts.length > 0 ? accounts[0].address : null;
    } catch {
        return null;
    }
}

/**
 * Get contract instance
 */
async function getContract(contractAddress: string): Promise<ethers.Contract> {
    if (!isMetaMaskInstalled()) {
        throw new Error('MetaMask is not installed');
    }

    const provider = new ethers.BrowserProvider((window as any).ethereum);
    const signer = await provider.getSigner();
    return new ethers.Contract(contractAddress, CONTRACT_ABI, signer);
}

/**
 * Record a flight event on blockchain via MetaMask
 * 
 * @param contractAddress - Address of the deployed FlightEventRegistry contract
 * @param flightId - Flight identifier (e.g., "UA123")
 * @param eventType - Type of event (e.g., "DEPARTURE")
 * @param timestamp - Unix timestamp
 * @param actor - Actor responsible (e.g., "SYSTEM")
 * @param dataHash - SHA256 hash of event data (0x-prefixed hex string)
 * @returns Transaction receipt
 */
export async function recordEventViaMetaMask(
    contractAddress: string,
    flightId: string,
    eventType: string,
    timestamp: number,
    actor: string,
    dataHash: string
): Promise<ethers.TransactionReceipt> {
    // Ensure account is connected
    await connectMetaMask();

    const contract = await getContract(contractAddress);
    
    // Convert dataHash to bytes32 (ensure it's 32 bytes)
    // ethers.js v6 handles hex strings directly, so we can use hexlify or ensure it's a hex string
    let dataHashHex: string;
    if (dataHash.startsWith('0x')) {
        dataHashHex = dataHash;
    } else {
        dataHashHex = '0x' + dataHash;
    }
    
    // Ensure it's exactly 66 characters (0x + 64 hex chars = 32 bytes)
    if (dataHashHex.length !== 66) {
        throw new Error('Data hash must be 32 bytes (64 hex characters)');
    }
    
    // Convert to bytes32 format that ethers expects
    const dataHashBytes32 = ethers.getBytes(dataHashHex);
    
    // Estimate gas
    const gasEstimate = await contract.recordEvent.estimateGas(
        flightId,
        eventType,
        timestamp,
        actor,
        dataHashBytes32
    );

    // Send transaction (MetaMask will prompt user)
    const tx = await contract.recordEvent(
        flightId,
        eventType,
        timestamp,
        actor,
        dataHashBytes32,
        {
            gasLimit: gasEstimate * BigInt(120) / BigInt(100) // Add 20% buffer
        }
    );

    // Wait for confirmation
    const receipt = await tx.wait();
    if (!receipt) {
        throw new Error('Transaction receipt is null');
    }
    return receipt;
}

/**
 * Read flight events from blockchain
 */
export async function getFlightEventsFromChain(
    contractAddress: string,
    flightId: string
): Promise<any[]> {
    // Add timeout to prevent hanging
    const timeout = 5000; // 5 seconds
    
    try {
        const providerPromise = isMetaMaskInstalled()
            ? new ethers.BrowserProvider((window as any).ethereum)
            : new ethers.JsonRpcProvider(
                process.env.NEXT_PUBLIC_GANACHE_URL || 'http://127.0.0.1:7545'
            );

        const provider = await Promise.race([
            providerPromise,
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Provider connection timeout')), timeout)
            )
        ]) as ethers.Provider;

        const contract = new ethers.Contract(contractAddress, CONTRACT_ABI, provider);
        
        // Add timeout for contract calls
        const indices = await Promise.race([
            contract.getFlightEventIndices(flightId),
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('Contract call timeout')), timeout)
            )
        ]) as bigint[];
        
        if (!indices || indices.length === 0) {
            return [];
        }
        
        const events = [];
        for (const index of indices) {
            try {
                // Call the getEvent function with the index (using getFunction to avoid type conflicts)
                const getEventFunc = contract.getFunction('getEvent');
                const eventData = await Promise.race([
                    getEventFunc(Number(index)),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Event fetch timeout')), timeout)
                    )
                ]) as any;
                
                events.push({
                    flightId: eventData[0],
                    eventType: eventData[1],
                    timestamp: Number(eventData[2]),
                    actor: eventData[3],
                    dataHash: typeof eventData[4] === 'string' ? eventData[4] : eventData[4].hex || eventData[4],
                    blockNumber: Number(eventData[5]),
                    recordedAt: Number(eventData[6])
                });
            } catch (error) {
                console.warn(`Failed to fetch event at index ${index}:`, error);
                // Continue with other events
            }
        }
        
        return events;
    } catch (error: any) {
        console.error('Error fetching events from chain:', error);
        // Return empty array instead of throwing - allows flow to continue
        return [];
    }
}

/**
 * Prepare transaction data for MetaMask
 * This is called from backend to prepare the transaction without executing it
 */
export interface PreparedTransaction {
    to: string;
    data: string;
    value: string;
    gas?: string;
}

/**
 * Prepare a transaction to record an event (without sending)
 */
export async function prepareRecordEventTransaction(
    contractAddress: string,
    flightId: string,
    eventType: string,
    timestamp: number,
    actor: string,
    dataHash: string
): Promise<PreparedTransaction> {
    const provider = new ethers.JsonRpcProvider(
        process.env.NEXT_PUBLIC_GANACHE_URL || 'http://127.0.0.1:8545'
    );
    const contract = new ethers.Contract(contractAddress, CONTRACT_ABI, provider);
    
    // Convert dataHash to bytes32
    let dataHashHex: string;
    if (dataHash.startsWith('0x')) {
        dataHashHex = dataHash;
    } else {
        dataHashHex = '0x' + dataHash;
    }
    
    // Ensure it's exactly 66 characters (0x + 64 hex chars = 32 bytes)
    if (dataHashHex.length !== 66) {
        throw new Error('Data hash must be 32 bytes (64 hex characters)');
    }
    
    // Convert to bytes32 format
    const dataHashBytes32 = ethers.getBytes(dataHashHex);
    
    const data = contract.interface.encodeFunctionData('recordEvent', [
        flightId,
        eventType,
        timestamp,
        actor,
        dataHashBytes32
    ]);

    // Estimate gas
    let gasEstimate: bigint;
    try {
        gasEstimate = await contract.recordEvent.estimateGas(
            flightId,
            eventType,
            timestamp,
            actor,
            dataHashBytes32
        );
    } catch {
        gasEstimate = BigInt(300000); // Default fallback
    }

    return {
        to: contractAddress,
        data,
        value: '0x0',
        gas: `0x${gasEstimate.toString(16)}`
    };
}

/**
 * Send prepared transaction via MetaMask
 */
export async function sendPreparedTransaction(
    transaction: PreparedTransaction
): Promise<ethers.TransactionReceipt | null> {
    console.log('sendPreparedTransaction called with:', transaction);
    
    if (!isMetaMaskInstalled()) {
        throw new Error('MetaMask is not installed. Please install MetaMask extension.');
    }

    console.log('Connecting to MetaMask...');
    await connectMetaMask();
    console.log('MetaMask connected');
    
    const provider = new ethers.BrowserProvider((window as any).ethereum);
    console.log('Provider created, getting signer...');
    const signer = await provider.getSigner();
    console.log('Signer obtained, preparing transaction...');
    
    try {
        // MetaMask will prompt user for approval - this is where MetaMask should open!
        console.log('Calling signer.sendTransaction() - MetaMask should open now!');
        const tx = await signer.sendTransaction({
            to: transaction.to,
            data: transaction.data,
            value: transaction.value,
            gasLimit: transaction.gas ? BigInt(transaction.gas) : undefined
        });
        console.log('Transaction sent, waiting for confirmation. TX hash:', tx.hash);

        const receipt = await tx.wait();
        console.log('Transaction confirmed! Receipt:', receipt);
        return receipt;
    } catch (error: any) {
        console.error('Error in sendPreparedTransaction:', error);
        // Re-throw with more context
        if (error.code === 4001) {
            throw new Error('User rejected transaction in MetaMask');
        } else if (error.message) {
            throw new Error(`MetaMask transaction failed: ${error.message}`);
        } else {
            throw error;
        }
    }
}
