'use client';

import React from 'react';
import { Card, Descriptions, Tag, Typography, Space, Row, Col } from 'antd';
import { EnvironmentOutlined, ClockCircleOutlined, SendOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { Flight } from '../types';

const { Title, Text } = Typography;

interface Props {
    flight: Flight;
}

export default function FlightSummary({ flight }: Props) {
    const getStatusColor = (status: string) => {
        switch (status.toUpperCase()) {
            case 'ARRIVED': return 'success';
            case 'AIRBORNE': return 'processing';
            case 'SCHEDULED': return 'default';
            case 'CANCELLED': return 'error';
            case 'DIVERTED': return 'warning';
            default: return 'default';
        }
    };

    const formatTime = (time?: string) => time ? dayjs(time).format('HH:mm') : '--:--';
    const formatDate = (time?: string) => time ? dayjs(time).format('D MMM YYYY') : '';

    return (
        <Card
            bordered={false}
            style={{ marginBottom: 24, overflow: 'hidden' }}
            title={
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', padding: '8px 0' }}>
                    <Space size="middle" align="baseline">
                        <Title level={2} style={{ margin: 0, color: '#1890ff' }}>{flight.flight_number}</Title>
                        <Tag color="geekblue" style={{ fontSize: 14, padding: '4px 10px' }}>{flight.airline?.name}</Tag>
                    </Space>
                    <Tag
                        color={getStatusColor(flight.status)}
                        style={{ fontSize: 16, padding: '6px 16px', borderRadius: 16, fontWeight: 600 }}
                    >
                        {flight.status}
                    </Tag>
                </div>
            }
        >
            {(flight as any).is_mock_data && (
                <div style={{ marginBottom: 24, padding: 16, background: '#fffbe6', border: '1px solid #ffe58f', borderRadius: 8 }}>
                    <Text type="warning">
                        ⚠️ <strong>Demo Data:</strong> This flight is using synthetic/mock data because it was not found in the CSV database.
                        The information shown may not match actual flight details.
                    </Text>
                </div>
            )}
            <Row gutter={[48, 24]}>
                {/* Route Info */}
                <Col xs={24} md={12}>
                    <div style={{
                        background: '#f9f9f9',
                        padding: 24,
                        borderRadius: 12,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between'
                    }}>
                        <div style={{ textAlign: 'left' }}>
                            <Title level={1} style={{ margin: 0, color: '#262626' }}>{flight.origin?.icao || 'N/A'}</Title>
                            <Text type="secondary" style={{ fontSize: 14 }}>{(flight.origin as any)?.city || flight.origin?.name || 'Origin'}</Text>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, padding: '0 16px' }}>
                            <SendOutlined style={{ fontSize: 28, color: '#1890ff', transform: 'rotate(90deg)', marginBottom: 8 }} />
                            <div style={{ height: 2, background: '#e8e8e8', width: '100%' }}></div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                            <Title level={1} style={{ margin: 0, color: '#262626' }}>{flight.destination?.icao || 'N/A'}</Title>
                            <Text type="secondary" style={{ fontSize: 14 }}>{(flight.destination as any)?.city || flight.destination?.name || 'Destination'}</Text>
                        </div>
                    </div>
                </Col>

                {/* Time Info */}
                <Col xs={24} md={12}>
                    <Card size="small" bordered={false} style={{ background: 'transparent' }}>
                        <Descriptions column={2} size="middle" labelStyle={{ color: '#8c8c8c' }} contentStyle={{ fontWeight: 500 }}>
                            <Descriptions.Item label="Scheduled Departure">{formatTime(flight.scheduled?.departure)}</Descriptions.Item>
                            <Descriptions.Item label="Actual Departure">{formatTime(flight.actual?.departure)}</Descriptions.Item>
                            <Descriptions.Item label="Scheduled Arrival">{formatTime(flight.scheduled?.arrival)}</Descriptions.Item>
                            <Descriptions.Item label="Actual Arrival">{formatTime(flight.actual?.arrival)}</Descriptions.Item>
                        </Descriptions>
                        <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #f0f0f0' }}>
                            <Space size="large">
                                <Text type="secondary">
                                    <ClockCircleOutlined /> <span style={{ marginLeft: 8 }}>{formatDate(flight.scheduled?.departure)}</span>
                                </Text>
                                {flight.callsign && (
                                    <Tag>Callsign: {flight.callsign}</Tag>
                                )}
                            </Space>
                        </div>
                    </Card>
                </Col>
            </Row>
        </Card>
    );
}

