'use client';

import React from 'react';
import { Collapse, Tag, Typography, Space, Tooltip } from 'antd';
import { CheckCircleOutlined, LinkOutlined, ClockCircleOutlined, UserOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { FlightEvent } from '../types';

const { Text } = Typography;
const { Panel } = Collapse;

interface Props {
    events?: FlightEvent[];
}

export default function EventTimeline({ events }: Props) {
    if (!events || events.length === 0) {
        return <Text type="secondary">No events recorded for this flight.</Text>;
    }

    return (
        <Collapse accordion bordered={false} style={{ background: 'transparent' }}>
            {events.map((event) => (
                <Panel
                    key={event.id}
                    header={
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                            <Space>
                                <Text strong>{event.event_type.replace('_', ' ')}</Text>
                                {event.blockchain.is_verified && (
                                    <Tooltip title="Verified on Blockchain">
                                        <CheckCircleOutlined style={{ color: '#52c41a' }} />
                                    </Tooltip>
                                )}
                            </Space>
                            <Space>
                                <Text type="secondary">
                                    <ClockCircleOutlined /> {dayjs(event.timestamp).format('HH:mm')}
                                </Text>
                            </Space>
                        </div>
                    }
                >
                    <Space direction="vertical" style={{ width: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Text type="secondary"><UserOutlined /> Source</Text>
                            <Text>{event.actor || 'System'}</Text>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <Text type="secondary">Date</Text>
                            <Text>{dayjs(event.timestamp).format('D MMM YYYY HH:mm:ss')}</Text>
                        </div>

                        <div style={{ marginTop: 8, padding: 12, background: '#f5f5f5', borderRadius: 6 }}>
                            <Text type="secondary" style={{ fontSize: 12 }}>DATA HASH (SHA-256)</Text>
                            <div style={{ fontFamily: 'monospace', fontSize: 12, wordBreak: 'break-all' }}>
                                {event.data_hash}
                            </div>
                        </div>

                        {event.blockchain.is_verified ? (
                            <div style={{ marginTop: 4 }}>
                                <Tag color="success">Verified on Blockchain</Tag>
                                {event.blockchain.tx_hash && (
                                    <Space style={{ marginTop: 4 }}>
                                        <LinkOutlined />
                                        <Text copyable={{ text: event.blockchain.tx_hash }} ellipsis style={{ maxWidth: 300 }}>
                                            Tx: {event.blockchain.tx_hash}
                                        </Text>
                                    </Space>
                                )}
                            </div>
                        ) : (
                            <Tag color="warning">Pending Verification</Tag>
                        )}
                    </Space>
                </Panel>
            ))}
        </Collapse>
    );
}
