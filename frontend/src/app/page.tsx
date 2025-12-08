'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input, Button, Typography, Card, Space, Row, Col, message, Modal } from 'antd';
import { SearchOutlined, SafetyCertificateOutlined, RocketOutlined, WalletOutlined } from '@ant-design/icons';
import { traceFlight, getContractAddress, fetchFlightData, getFlightEventsFromChain, prepareTransaction, confirmTransaction } from '@/services/api';
import api from '@/services/api';
import { isMetaMaskInstalled, connectMetaMask, sendPreparedTransaction } from '@/services/web3';
import BlockchainConsole from '@/components/BlockchainConsole';

const { Title, Text, Paragraph } = Typography;

export default function Home() {
    const [flightNumber, setFlightNumber] = useState('');
    const [loading, setLoading] = useState(false);
    const [consoleVisible, setConsoleVisible] = useState(false);
    const [logs, setLogs] = useState<any[]>([]);
    const [metamaskModalVisible, setMetamaskModalVisible] = useState(false);
    const [pendingTransactions, setPendingTransactions] = useState<any[]>([]);
    const router = useRouter();

    const addLog = (type: string, msg: string) => {
        setLogs(prev => [...prev, { type, message: msg }]);
    };

    const handleSearch = async () => {
        if (!flightNumber.trim()) return;
        setLoading(true);
        setConsoleVisible(true);
        setLogs([]);

        try {
            // 1. Check if MetaMask is installed
            if (!isMetaMaskInstalled()) {
                addLog('error', 'MetaMask is not installed. Please install MetaMask to continue.');
                setLoading(false);
                return;
            }

            addLog('info', `Connecting to MetaMask...`);
            
            // 2. Connect to MetaMask
            try {
                await connectMetaMask();
                addLog('success', 'MetaMask connected successfully');
            } catch (error: any) {
                addLog('error', `MetaMask connection failed: ${error.message}`);
                setLoading(false);
                return;
            }

            // 3. Get contract address
            addLog('info', 'Fetching contract address...');
            const contractAddress = await getContractAddress();
            if (!contractAddress) {
                addLog('error', 'Contract address not configured. Please deploy the contract first.');
                setLoading(false);
                return;
            }
            addLog('success', `Contract address: ${contractAddress}`);

            // 4. Check blockchain for existing events (with short timeout to avoid hanging)
            addLog('info', `Checking blockchain for flight ${flightNumber.toUpperCase()}...`);
            let hasBlockchainEvents = false;
            try {
                // Very short timeout - if blockchain is slow, skip it
                const chainEventsPromise = getFlightEventsFromChain(contractAddress, flightNumber.toUpperCase());
                const timeoutPromise = new Promise<never>((_, reject) => 
                    setTimeout(() => reject(new Error('Blockchain query timeout - skipping')), 3000)
                );
                
                const chainEvents = await Promise.race([chainEventsPromise, timeoutPromise]);
                if (chainEvents && chainEvents.length > 0) {
                    addLog('success', `Found ${chainEvents.length} events on blockchain`);
                    hasBlockchainEvents = true;
                } else {
                    addLog('info', 'No events found on blockchain, will fetch from CSV database');
                }
            } catch (error: any) {
                // Silently continue - blockchain check is optional
                addLog('info', 'Blockchain check skipped, proceeding to fetch flight data...');
            }
            
            // If we found events on blockchain, go to flight page
            if (hasBlockchainEvents) {
                setTimeout(() => {
                    router.push(`/flight/${flightNumber.toUpperCase()}`);
                    setLoading(false);
                }, 1500);
                return;
            }

            // 5. Flight not on blockchain - fetch from CSV database and create events
            addLog('info', 'Flight not found on blockchain. Fetching from CSV database...');
            try {
                const traceLogs = await traceFlight(flightNumber.toUpperCase());
                // Ensure all logs have the required structure
                const validTraceLogs = Array.isArray(traceLogs) 
                    ? traceLogs.filter((log: any) => log && log.type && log.message)
                    : [];
                setLogs(prev => [...prev, ...validTraceLogs]);

                // Check if traceFlight succeeded (created flight)
                // Only fail if there's a critical error about flight creation, not blockchain connection errors
                const criticalErrors = validTraceLogs.filter((log: any) => 
                    log.type === 'error' && 
                    (log.message.includes('Oracle failed') || log.message.includes('failed to retrieve flight'))
                );
                
                if (criticalErrors.length > 0) {
                    addLog('error', 'Failed to create flight. Please try again.');
                    setLoading(false);
                    return;
                }
                
                // Blockchain connection errors are not critical - flight can still be created
                const blockchainErrors = validTraceLogs.filter((log: any) => 
                    log.type === 'error' && log.message.includes('contract')
                );
                if (blockchainErrors.length > 0) {
                    addLog('warning', 'Blockchain connection issue detected. Events will still be created in database.');
                }

                // Wait a moment for database to commit - events need time to be created
                addLog('info', 'Waiting for database synchronization (events being created)...');
                await new Promise(resolve => setTimeout(resolve, 3000)); // Increased to 3 seconds

                // 6. Get flight data to find events that need to be recorded
                addLog('info', 'Fetching flight data and events...');
                let flightData;
                let fetchAttempts = 0;
                const maxFetchAttempts = 8; // Increased attempts
                
                // Retry fetching until we get events or max attempts reached
                while (fetchAttempts < maxFetchAttempts) {
                    try {
                        flightData = await fetchFlightData(flightNumber.toUpperCase(), 1);
                        
                        // Check if we got events
                        if (flightData && flightData.events && flightData.events.length > 0) {
                            addLog('success', `Flight data retrieved with ${flightData.events.length} events`);
                            console.log('✓ Events found:', flightData.events.length);
                            break;
                        } else {
                            fetchAttempts++;
                            console.log(`✗ Attempt ${fetchAttempts}/${maxFetchAttempts}: Events not found. FlightData:`, {
                                hasFlightData: !!flightData,
                                eventsLength: flightData?.events?.length || 0,
                                events: flightData?.events
                            });
                            
                            if (fetchAttempts < maxFetchAttempts) {
                                addLog('info', `Events not ready yet, retrying... (attempt ${fetchAttempts}/${maxFetchAttempts})`);
                                await new Promise(resolve => setTimeout(resolve, 2000)); // Increased wait time
                            } else {
                                addLog('warning', 'Events may still be processing. Will check flight page...');
                                console.log('⚠ Max attempts reached. FlightData:', flightData);
                            }
                        }
                    } catch (error: any) {
                        fetchAttempts++;
                        const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Unknown error';
                        console.error('Flight fetch error details:', {
                            message: errorMsg,
                            response: error.response?.data,
                            flightNumber: flightNumber.toUpperCase()
                        });
                        
                        if (fetchAttempts >= maxFetchAttempts) {
                            addLog('error', `Failed to fetch flight data after ${maxFetchAttempts} attempts: ${errorMsg}`);
                            
                            // Check if the search endpoint can find the flight
                            addLog('info', 'Attempting direct flight search...');
                            try {
                                const searchRes = await api.get(`/search-flight/${flightNumber.toUpperCase()}`);
                                if (searchRes.data.found) {
                                    addLog('success', 'Flight found via direct search. Proceeding...');
                                    // Use the found flight data - but try to fetch events separately
                                    const flightId = searchRes.data.flight.id;
                                    try {
                                        const eventsRes = await api.get(`/flight/${flightId}/events`);
                                        addLog('success', `Found ${eventsRes.data.length} events via direct API call`);
                                        flightData = {
                                            ...searchRes.data.flight,
                                            events: eventsRes.data || [],
                                            delayAnalysis: null,
                                            blockchainEvents: [],
                                            historicalBaseline: null
                                        };
                                    } catch (eventsError: any) {
                                        console.warn('Could not fetch events:', eventsError);
                                        flightData = {
                                            ...searchRes.data.flight,
                                            events: [],
                                            delayAnalysis: null,
                                            blockchainEvents: [],
                                            historicalBaseline: null
                                        };
                                    }
                                } else {
                                    throw new Error(searchRes.data.message || 'Flight not found');
                                }
                            } catch (searchError: any) {
                                addLog('warning', 'Flight not found in database. This may be expected for new flights.');
                                // Navigate anyway - the flight page will handle missing data
                                setTimeout(() => {
                                    router.push(`/flight/${flightNumber.toUpperCase()}`);
                                }, 2000);
                                setLoading(false);
                                return;
                            }
                            break;
                        } else {
                            addLog('info', `Retrying flight fetch... (attempt ${fetchAttempts}/${maxFetchAttempts})`);
                            await new Promise(resolve => setTimeout(resolve, 2000)); // Increased wait time
                        }
                    }
                }
                
                if (!flightData) {
                    addLog('error', 'Flight data not found. Please try again.');
                    setLoading(false);
                    return;
                }
                
                addLog('info', 'Flight data retrieved successfully');
                
                // Debug: Log events structure
                console.log('=== FLIGHT DATA DEBUG ===');
                console.log('Flight data:', flightData);
                console.log('Events:', flightData.events);
                console.log('Events length:', flightData.events?.length);
                console.log('Events type:', typeof flightData.events);
                console.log('Is array:', Array.isArray(flightData.events));
                
                if (flightData.events && flightData.events.length > 0) {
                    addLog('info', `Found ${flightData.events.length} total events`);
                    
                    // Debug: Log event structure
                    flightData.events.forEach((e: any, idx: number) => {
                        console.log(`Event ${idx}:`, {
                            id: e.id,
                            event_type: e.event_type,
                            blockchain: e.blockchain,
                            is_verified: e.blockchain?.is_verified
                        });
                    });
                    
                    // Process events that need blockchain recording
                    const eventsNeedingTx = flightData.events.filter((e: any) => {
                        const isVerified = e.blockchain?.is_verified;
                        console.log(`Event ${e.id} (${e.event_type}): is_verified=${isVerified}`);
                        return !isVerified;
                    });
                    
                    addLog('info', `${eventsNeedingTx.length} events need blockchain recording (out of ${flightData.events.length} total)`);
                    
                    if (eventsNeedingTx.length > 0) {
                        addLog('info', `Found ${eventsNeedingTx.length} events that need to be recorded on blockchain`);
                        addLog('warning', 'MetaMask will open to approve transactions. You will pay minimal gas fees.');
                        
                        // Prepare transactions via backend API
                        addLog('info', 'Preparing transactions for MetaMask...');
                        const transactions = [];
                        for (const event of eventsNeedingTx) {
                            try {
                                const preparedTx = await prepareTransaction(event.id);
                                transactions.push({
                                    event,
                                    transaction: preparedTx
                                });
                                addLog('success', `✓ Prepared transaction for ${event.event_type}`);
                            } catch (error: any) {
                                const errorMsg = error.response?.data?.detail || error.message;
                                addLog('error', `✗ Failed to prepare transaction for ${event.event_type}: ${errorMsg}`);
                                console.error('Transaction preparation error:', error);
                                
                                // If it's a connection error, provide helpful message
                                if (errorMsg.includes('Cannot connect') || errorMsg.includes('Ganache')) {
                                    addLog('error', 'Make sure Ganache is running on port 7545');
                                }
                                if (errorMsg.includes('Contract address')) {
                                    addLog('error', 'Contract address not configured in backend .env file');
                                }
                            }
                        }
                        
                        if (transactions.length > 0) {
                            addLog('success', `Successfully prepared ${transactions.length} transaction(s)`);
                            addLog('warning', '⚠️ IMPORTANT: A modal will appear! Click "Approve & Send" in the modal to open MetaMask!');
                            
                            console.log('=== OPENING METAMASK MODAL ===');
                            console.log('Transactions prepared:', transactions.length);
                            console.log('Setting pending transactions:', transactions);
                            
                            // CRITICAL: Set state synchronously and ensure modal shows IMMEDIATELY on home page
                            setPendingTransactions(transactions);
                            setLoading(false); // Stop loading spinner
                            setMetamaskModalVisible(true); // Show modal immediately - no delay!
                            
                            console.log('✅ Modal set to visible IMMEDIATELY on home page');
                            console.log('✅ Transactions ready:', transactions.length);
                            console.log('✅ Modal should be visible NOW - no navigation yet');
                            
                            // Return here to prevent navigation - modal will handle navigation after user action
                            return;
                        } else {
                            addLog('error', `No transactions were prepared successfully. ${eventsNeedingTx.length} events need recording but preparation failed.`);
                            addLog('error', 'Could not prepare any transactions. Please check:');
                            addLog('error', '1. Is Ganache running on port 7545?');
                            addLog('error', '2. Is CONTRACT_ADDRESS set in backend .env?');
                            addLog('error', '3. Is the contract deployed at the configured address?');
                            addLog('warning', 'You can still record events manually from the flight page.');
                            setTimeout(() => {
                                router.push(`/flight/${flightNumber.toUpperCase()}`);
                            }, 3000);
                            setLoading(false);
                            return;
                        }
                    } else {
                        addLog('success', 'All events are already on blockchain');
                        setTimeout(() => {
                            router.push(`/flight/${flightNumber.toUpperCase()}`);
                        }, 2000);
                        setLoading(false);
                        return;
                    }
                } else {
                    console.log('=== NO EVENTS FOUND ===');
                    console.log('Flight data:', flightData);
                    console.log('Events array:', flightData.events);
                    console.log('Flight ID:', flightData?.id);
                    
                    // Try to fetch events directly if we have a flight ID
                    if (flightData && flightData.id) {
                        addLog('info', `Attempting to fetch events directly for flight ID ${flightData.id}...`);
                        try {
                            const eventsRes = await api.get(`/flight/${flightData.id}/events`);
                            if (eventsRes.data && eventsRes.data.length > 0) {
                                addLog('success', `Found ${eventsRes.data.length} events via direct API call`);
                                flightData.events = eventsRes.data;
                                
                                // Now process events - same logic as above
                                const eventsNeedingTxDirect = flightData.events.filter((e: any) => !e.blockchain?.is_verified);
                                addLog('info', `${eventsNeedingTxDirect.length} events need blockchain recording (out of ${flightData.events.length} total)`);
                                
                                if (eventsNeedingTxDirect.length > 0) {
                                    addLog('info', `Found ${eventsNeedingTxDirect.length} events that need to be recorded on blockchain`);
                                    addLog('warning', 'MetaMask will open to approve transactions. You will pay minimal gas fees.');
                                    
                                    // Prepare transactions via backend API
                                    addLog('info', 'Preparing transactions for MetaMask...');
                                    const transactions = [];
                                    for (const event of eventsNeedingTxDirect) {
                                        try {
                                            const preparedTx = await prepareTransaction(event.id);
                                            transactions.push({
                                                event,
                                                transaction: preparedTx
                                            });
                                            addLog('success', `✓ Prepared transaction for ${event.event_type}`);
                                        } catch (error: any) {
                                            const errorMsg = error.response?.data?.detail || error.message;
                                            addLog('error', `✗ Failed to prepare transaction for ${event.event_type}: ${errorMsg}`);
                                            console.error('Transaction preparation error:', error);
                                        }
                                    }
                                    
                                    if (transactions.length > 0) {
                                        addLog('success', `Successfully prepared ${transactions.length} transaction(s)`);
                                        addLog('warning', '⚠️ IMPORTANT: A modal will appear! Click "Approve & Send" in the modal to open MetaMask!');
                                        
                                        console.log('=== OPENING METAMASK MODAL (DIRECT FETCH) ===');
                                        
                                        setPendingTransactions(transactions);
                                        setLoading(false); // Stop loading spinner
                                        setMetamaskModalVisible(true); // Show modal immediately - no delay!
                                        
                                        console.log('✅ Modal set to visible IMMEDIATELY on home page (direct fetch path)');
                                        console.log('✅ Transactions ready:', transactions.length);
                                        console.log('✅ Modal should be visible NOW - no navigation yet');
                                        
                                        // Return here to prevent navigation - modal will handle navigation after user action
                                        return;
                                    }
                                } else {
                                    addLog('success', 'All events are already verified on blockchain');
                                    setTimeout(() => {
                                        router.push(`/flight/${flightNumber.toUpperCase()}`);
                                    }, 2000);
                                    setLoading(false);
                                    return;
                                }
                            } else {
                                throw new Error('No events in response');
                            }
                        } catch (eventsError: any) {
                            console.error('Direct event fetch failed:', eventsError);
                            addLog('warning', `Could not fetch events directly: ${eventsError.message}`);
                            addLog('info', 'Events might still be being created. Check the flight page for "Record Events on Blockchain" button.');
                            addLog('warning', 'Proceeding to flight page where you can manually record events...');
                            setTimeout(() => {
                                router.push(`/flight/${flightNumber.toUpperCase()}`);
                            }, 2000);
                            setLoading(false);
                            return;
                        }
                    } else {
                        addLog('warning', `No events found in flight data. Events array: ${flightData.events ? 'exists but empty' : 'missing'}`);
                        addLog('info', 'Events might still be being created. Check the flight page for "Record Events on Blockchain" button.');
                        addLog('warning', 'Proceeding to flight page where you can manually record events...');
                        setTimeout(() => {
                            router.push(`/flight/${flightNumber.toUpperCase()}`);
                        }, 2000);
                        setLoading(false);
                        return;
                    }
                }
            } catch (error: any) {
                addLog('error', `Error during flight processing: ${error.response?.data?.detail || error.message}`);
                message.error('Failed to process flight search. Please try again.');
                setLoading(false);
            }

        } catch (error: any) {
            console.error(error);
            addLog('error', `Error: ${error.message}`);
            message.error("Failed to process flight search");
            setLoading(false);
        }
        // Note: Removed finally block - loading state is now managed explicitly to prevent interfering with modal
    };

    const handleApproveTransactions = async () => {
        if (pendingTransactions.length === 0) {
            addLog('error', 'No pending transactions to approve');
            return;
        }
        
        addLog('info', `Starting MetaMask transaction flow for ${pendingTransactions.length} transaction(s)...`);
        console.log('handleApproveTransactions called with', pendingTransactions.length, 'transactions');
        
        // Keep modal open during processing to show progress
        // setMetamaskModalVisible(false); // Don't close yet
        
        for (let i = 0; i < pendingTransactions.length; i++) {
            const { event, transaction } = pendingTransactions[i];
            try {
                addLog('info', `⏳ Opening MetaMask for transaction ${i + 1}/${pendingTransactions.length} (${event.event_type})...`);
                console.log('Sending transaction', i + 1, 'via MetaMask');
                
                // This should trigger MetaMask to open
                const receipt = await sendPreparedTransaction(transaction);
                
                if (!receipt) {
                    addLog('error', 'Transaction receipt is null - transaction may have failed');
                    continue;
                }
                
                addLog('success', `✅ Transaction ${i + 1} confirmed! Block ${receipt.blockNumber}, Hash ${receipt.hash.slice(0, 10)}...`);
                console.log('Transaction confirmed:', receipt.hash);
                
                // Confirm transaction in backend
                try {
                    await confirmTransaction(event.id, receipt.hash, Number(receipt.blockNumber));
                    addLog('info', `✓ Transaction recorded in database`);
                } catch (confirmError: any) {
                    addLog('warning', `⚠ Transaction confirmed on blockchain but failed to update database: ${confirmError.message}`);
                }
            } catch (error: any) {
                console.error('Transaction error:', error);
                if (error.code === 4001) {
                    addLog('error', '❌ Transaction rejected by user in MetaMask');
                    message.error('Transaction was rejected. Please try again.');
                    break;
                } else if (error.message?.includes('MetaMask')) {
                    addLog('error', `❌ MetaMask error: ${error.message}`);
                    message.error(`MetaMask error: ${error.message}`);
                } else {
                    addLog('error', `❌ Transaction failed: ${error.message || JSON.stringify(error)}`);
                    message.error(`Transaction failed: ${error.message || 'Unknown error'}`);
                }
            }
        }
        
        // Close modal after all transactions
        setMetamaskModalVisible(false);
        
        addLog('success', 'All transactions processed successfully!');
        addLog('info', 'Navigating to flight details page...');
        
        // Navigate directly to flight page - it will reload data and show updated verification status
        // Don't wait for blockchain reads as they may timeout
        setLoading(false);
        setTimeout(() => {
            router.push(`/flight/${flightNumber.toUpperCase()}`);
        }, 1000);
    };

    const handleConsoleComplete = () => {
        // Only navigate if modal is not visible - if modal is showing, let user approve transactions first
        // Don't navigate automatically - wait for user action on modal
        if (!metamaskModalVisible && !loading && flightNumber) {
            // Only auto-navigate if no transactions pending
        router.push(`/flight/${flightNumber.toUpperCase()}`);
        }
    };

    return (
        <main style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '70vh'
        }}>
            <div style={{ maxWidth: 800, width: '100%', textAlign: 'center' }}>
                <Space direction="vertical" size="large" style={{ width: '100%' }}>

                    <div style={{ marginBottom: 40 }}>
                        <SafetyCertificateOutlined style={{ fontSize: 64, color: '#1890ff', marginBottom: 24 }} />
                        <Title level={1}>FlightChain</Title>
                        <Paragraph style={{ fontSize: 18, color: '#666' }}>
                            The world's first blockchain-verified flight event tracking system.
                            <br />
                            Transparent, immutable, and trusted real-time flight data.
                        </Paragraph>
                    </div>

                    <div style={{ textAlign: 'left', marginBottom: 20 }}>
                        <BlockchainConsole
                            logs={logs}
                            visible={consoleVisible}
                            onComplete={handleConsoleComplete}
                        />
                    </div>

                    {/* Modal should be visible even when console is showing */}
                    {consoleVisible && metamaskModalVisible && (
                        <div style={{ marginTop: 20, textAlign: 'center' }}>
                            <Text type="warning" strong>
                                ⚠️ Please review and approve transactions in the modal above!
                            </Text>
                        </div>
                    )}

                    {!consoleVisible && (
                        <Card
                            hoverable
                            style={{
                                borderRadius: 12,
                                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                                padding: 24
                            }}
                        >
                            <Space.Compact size="large" style={{ width: '100%', maxWidth: 500 }}>
                                <Input
                                    placeholder="Enter flight number (e.g., UA123, AA456)"
                                    value={flightNumber}
                                    onChange={(e) => setFlightNumber(e.target.value)}
                                    onPressEnter={handleSearch}
                                    prefix={<RocketOutlined style={{ color: '#bfbfbf' }} />}
                                    style={{ width: 'calc(100% - 100px)' }}
                                    allowClear
                                />
                                <Button
                                    type="primary"
                                    icon={<SearchOutlined />}
                                    loading={loading}
                                    onClick={handleSearch}
                                    style={{ width: 100 }}
                                >
                                    Search
                                </Button>
                            </Space.Compact>
                        </Card>
                    )}

                    <Row gutter={24} style={{ marginTop: 48 }}>
                        <Col span={8}>
                            <Card bordered={false}>
                                <Title level={4}>Real-Time Tracking</Title>
                                <Text type="secondary">Live event updates from OpenSky Network ingestion.</Text>
                            </Card>
                        </Col>
                        <Col span={8}>
                            <Card bordered={false}>
                                <Title level={4}>Blockchain Verified</Title>
                                <Text type="secondary">Every event is hashed and recorded on Ethereum.</Text>
                            </Card>
                        </Col>
                        <Col span={8}>
                            <Card bordered={false}>
                                <Title level={4}>Smart Analysis</Title>
                                <Text type="secondary">Automated delay reasoning and historical insights.</Text>
                            </Card>
                        </Col>
                    </Row>

                </Space>
            </div>

            <Modal
                title={
                    <Space>
                        <WalletOutlined style={{ color: '#1890ff' }} />
                        <span>Approve MetaMask Transactions</span>
                    </Space>
                }
                open={metamaskModalVisible}
                onOk={handleApproveTransactions}
                onCancel={() => {
                    setMetamaskModalVisible(false);
                    setPendingTransactions([]);
                    message.warning('Transactions cancelled. Events will not be recorded on blockchain.');
                    setTimeout(() => {
                        router.push(`/flight/${flightNumber.toUpperCase()}`);
                    }, 1000);
                }}
                okText="Approve & Send (Opens MetaMask)"
                cancelText="Skip for Now"
                width={650}
                maskClosable={false}
                closable={true}
                zIndex={10000}
                style={{ top: 50 }}
            >
                <div style={{ marginBottom: 16 }}>
                    <Text strong style={{ fontSize: 16 }}>
                        ⚠️ Click "Approve & Send" below to open MetaMask!
                    </Text>
                </div>
                <div style={{ marginBottom: 16 }}>
                    <Text>
                        You need to approve <strong>{pendingTransactions.length} transaction(s)</strong> to record flight events on the blockchain.
                    </Text>
                </div>
                <div style={{ marginBottom: 16, padding: 12, background: '#e6f7ff', border: '1px solid #91d5ff', borderRadius: 4 }}>
                    <Text type="secondary">
                        <strong>What happens next:</strong><br/>
                        1. Click "Approve & Send" button below<br/>
                        2. MetaMask window will open automatically<br/>
                        3. Approve each transaction in MetaMask ({pendingTransactions.length} total)<br/>
                        4. Gas fees are minimal (free on Ganache testnet)
                    </Text>
                </div>
                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                    <Text strong>Events to record:</Text>
                    <ul style={{ marginTop: 8, marginBottom: 0 }}>
                        {pendingTransactions.map((tx, idx) => (
                            <li key={idx}>
                                <Text code>{tx.event.event_type}</Text> - {new Date(tx.event.timestamp).toLocaleString()}
                            </li>
                        ))}
                    </ul>
                </div>
            </Modal>
        </main>
    );
}
