'use client';

import React, { useEffect, useState } from 'react';
import { Tabs, Card, Spin, Result, Row, Col, Button, Modal, message, Space, Typography } from 'antd';

const { Text } = Typography;
import { useParams } from 'next/navigation';
import { RocketOutlined, BlockOutlined, LineChartOutlined, WalletOutlined } from '@ant-design/icons';

import FlightSummary from '@/components/FlightSummary';
import AircraftMetadata from '@/components/AircraftMetadata';
import DelaySummary from '@/components/DelaySummary';
import EventTimeline from '@/components/EventTimeline';
import BlockchainLog from '@/components/BlockchainLog';
import HistoricalBaselineView from '@/components/HistoricalBaseline';

import { fetchFlightData, prepareTransaction, confirmTransaction, getContractAddress } from '@/services/api';
import { isMetaMaskInstalled, connectMetaMask, sendPreparedTransaction } from '@/services/web3';
import { Flight } from '@/types';

export default function FlightPage() {
    const { flightId } = useParams();
    const [flight, setFlight] = useState<Flight | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [recording, setRecording] = useState(false);
    const [metamaskModalVisible, setMetamaskModalVisible] = useState(false);
    const [pendingTransactions, setPendingTransactions] = useState<any[]>([]);

    useEffect(() => {
        if (flightId) {
            loadFlightData(flightId as string);
        }
    }, [flightId]);

    const loadFlightData = async (id: string) => {
        try {
            setLoading(true);
            setError(null);
            
            console.log('Loading flight data for:', id);
            
            // fetchFlightData handles both flight numbers and IDs
            // It first searches by flight number, then uses the returned flight ID
            const data = await fetchFlightData(id);
            
            if (data) {
                console.log('Flight data loaded:', data.id, data.flight_number);
                setFlight(data);
            } else {
                throw new Error('Flight data not found');
            }
        } catch (err: any) {
            console.error('Error loading flight data:', err);
            const errorMsg = err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to load flight data';
            setError(errorMsg);
            
            // If it's a 404 or "not found", show helpful message
            if (err.response?.status === 404 || errorMsg.toLowerCase().includes('not found')) {
                setError(`Flight "${id}" not found. The flight may not exist in the database yet.`);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleRecordOnBlockchain = async () => {
        if (!flight || !flight.events || flight.events.length === 0) {
            message.warning('No events to record');
            return;
        }

        // Check MetaMask
        if (!isMetaMaskInstalled()) {
            message.error('MetaMask is not installed. Please install MetaMask to record events on blockchain.');
            return;
        }

        try {
            await connectMetaMask();
        } catch (error: any) {
            message.error(`MetaMask connection failed: ${error.message}`);
            return;
        }

        // Find events that need to be recorded
        const eventsNeedingTx = flight.events.filter((e: any) => !e.blockchain?.is_verified);
        
        if (eventsNeedingTx.length === 0) {
            message.success('All events are already recorded on blockchain');
            return;
        }

        setRecording(true);
        message.info(`Preparing ${eventsNeedingTx.length} transaction(s)...`);

        try {
            const contractAddress = await getContractAddress();
            if (!contractAddress) {
                message.error('Contract address not configured');
                setRecording(false);
                return;
            }

            // Prepare transactions
            const transactions = [];
            const errors: string[] = [];
            for (const event of eventsNeedingTx) {
                try {
                    const preparedTx = await prepareTransaction(event.id);
                    if (preparedTx && preparedTx.to && preparedTx.data) {
                        transactions.push({
                            event,
                            transaction: preparedTx
                        });
                        console.log(`✓ Prepared transaction for ${event.event_type}`);
                    } else {
                        errors.push(`Invalid transaction data for ${event.event_type}`);
                    }
                } catch (error: any) {
                    const errorMsg = error.response?.data?.detail || error.message || 'Unknown error';
                    errors.push(`${event.event_type}: ${errorMsg}`);
                    console.error(`Failed to prepare transaction for ${event.event_type}:`, error);
                }
            }

            if (errors.length > 0) {
                console.error('Transaction preparation errors:', errors);
                message.warning(`${errors.length} transaction(s) failed to prepare. Check console for details.`);
            }

            if (transactions.length > 0) {
                message.success(`Successfully prepared ${transactions.length} transaction(s)`);
                setPendingTransactions(transactions);
                setMetamaskModalVisible(true);
            } else {
                message.error(`Failed to prepare any transactions. ${errors.length > 0 ? errors[0] : 'Check blockchain connection and contract address.'}`);
            }
        } catch (error: any) {
            message.error(`Error: ${error.message}`);
        } finally {
            setRecording(false);
        }
    };

    const handleApproveTransactions = async () => {
        if (pendingTransactions.length === 0) return;

        setMetamaskModalVisible(false);
        setRecording(true);
        
        // Important: MetaMask doesn't auto-open popups due to browser security
        // Show a notification to the user
        message.warning({
            content: 'Please check MetaMask! It should open automatically, but if not, click the MetaMask extension icon in your browser.',
            duration: 5,
        });

        let successCount = 0;
        for (let i = 0; i < pendingTransactions.length; i++) {
            const { event, transaction } = pendingTransactions[i];
            try {
                message.info(`⏳ Waiting for MetaMask approval for transaction ${i + 1}/${pendingTransactions.length}...`);
                
                // Small delay to ensure MetaMask is ready
                await new Promise(resolve => setTimeout(resolve, 500));
                
                const receipt = await sendPreparedTransaction(transaction);
                
                if (!receipt) {
                    message.error(`Transaction ${i + 1} failed: Receipt is null`);
                    continue;
                }
                
                // Confirm transaction in backend
                await confirmTransaction(event.id, receipt.hash, Number(receipt.blockNumber));
                successCount++;
                message.success(`Transaction ${i + 1} confirmed!`);
            } catch (error: any) {
                if (error.code === 4001) {
                    message.warning('Transaction rejected by user');
                    break;
                } else {
                    message.error(`Transaction ${i + 1} failed: ${error.message}`);
                }
            }
        }

        if (successCount > 0) {
            message.success(`Successfully recorded ${successCount} event(s) on blockchain!`);
            // Reload flight data
            await loadFlightData(flightId as string);
        }

        setRecording(false);
        setPendingTransactions([]);
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
                <Spin size="large" tip="Locating flight on blockchain..." />
            </div>
        );
    }

    if (error || !flight) {
        return (
            <Result
                status="error"
                title="Flight Not Found"
                subTitle={error || "We couldn't locate this flight in our system."}
            />
        );
    }

    const items = [
        {
            key: '1',
            label: <span><RocketOutlined /> Event Timeline</span>,
            children: <EventTimeline events={flight.events} />,
        },
        {
            key: '2',
            label: <span><BlockOutlined /> Blockchain Log</span>,
            children: <BlockchainLog events={flight.blockchainEvents} />,
        },
        {
            key: '3',
            label: <span><LineChartOutlined /> Historical Baseline</span>,
            children: <HistoricalBaselineView flight={flight} />,
        },
    ];

    return (
        <div className="flight-page">
            <FlightSummary flight={flight} />

            <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
                <Col xs={24} md={12}>
                    <AircraftMetadata aircraft={flight.aircraft} />
                </Col>
                <Col xs={24} md={12}>
                    <DelaySummary delayAnalysis={flight.delayAnalysis} />
                </Col>
            </Row>

            <Card style={{ borderRadius: 8 }}>
                <Tabs defaultActiveKey="1" items={items} />
            </Card>

            {/* Record on Blockchain Button */}
            {flight.events && flight.events.length > 0 && 
             (!flight.blockchainEvents || flight.blockchainEvents.length === 0) && (
                <Card style={{ marginTop: 24, textAlign: 'center' }}>
                    <Space direction="vertical" size="middle">
                        <div>
                            <p style={{ marginBottom: 8 }}>
                                <strong>{flight.events.filter((e: any) => !e.blockchain?.is_verified).length}</strong> event(s) ready to be recorded on blockchain
                            </p>
                            <p style={{ color: '#666', fontSize: 12 }}>
                                Record flight events immutably on the Ethereum blockchain via MetaMask
                            </p>
                        </div>
                        <Button
                            type="primary"
                            size="large"
                            icon={<WalletOutlined />}
                            loading={recording}
                            onClick={handleRecordOnBlockchain}
                        >
                            Record Events on Blockchain
                        </Button>
                    </Space>
                </Card>
            )}

            <div style={{ marginTop: 24, textAlign: 'center', color: '#999', fontSize: 12 }}>
                Blockchain Contract: <span style={{ fontFamily: 'monospace' }}>{flight.blockchainEvents?.[0]?.contract_address || 'Not recorded'}</span>
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
                }}
                okText="Approve & Send (Opens MetaMask)"
                cancelText="Skip for Now"
                width={600}
            >
                <div style={{ marginBottom: 16 }}>
                    <Text strong style={{ fontSize: 16 }}>
                        ⚠️ Click "Approve & Send" below to open MetaMask!
                    </Text>
                </div>
                <div style={{ marginBottom: 16 }}>
                    <p>You need to approve <strong>{pendingTransactions.length}</strong> transaction(s) to record flight events on the blockchain.</p>
                </div>
                <div style={{ marginBottom: 16, padding: 12, background: '#fff7e6', border: '1px solid #ffd591', borderRadius: 4 }}>
                    <Text type="warning">
                        <strong>Note:</strong> MetaMask may not auto-open due to browser popup blockers.<br/>
                        If MetaMask doesn't open automatically, click the MetaMask extension icon in your browser toolbar.
                    </Text>
                </div>
                <div style={{ marginBottom: 16, padding: 12, background: '#e6f7ff', border: '1px solid #91d5ff', borderRadius: 4 }}>
                    <Text type="secondary">
                        <strong>What happens next:</strong><br/>
                        1. Click "Approve & Send" button below<br/>
                        2. Check MetaMask (it should open automatically, but may require clicking the extension icon)<br/>
                        3. Approve each transaction in MetaMask ({pendingTransactions.length} total)<br/>
                        4. Gas fees are minimal (free on Ganache testnet)
                    </Text>
                </div>
                <div style={{ background: '#f5f5f5', padding: 12, borderRadius: 4 }}>
                    <strong>Events to record:</strong>
                    <ul style={{ marginTop: 8, marginBottom: 0 }}>
                        {pendingTransactions.map((tx, idx) => (
                            <li key={idx}>
                                <code>{tx.event.event_type}</code> - {new Date(tx.event.timestamp).toLocaleString()}
                            </li>
                        ))}
                    </ul>
                </div>
            </Modal>
        </div>
    );
}
