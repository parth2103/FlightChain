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
            style={{ marginBottom: 24, borderRadius: 8 }}
            title={
                <Space size="large">
                    <Title level={3} style={{ margin: 0 }}>{flight.flight_number}</Title>
                    <Tag color="blue">{flight.airline?.name}</Tag>
                    <Tag color={getStatusColor(flight.status)}>{flight.status}</Tag>
                </Space>
            }
        >
            {(flight as any).is_mock_data && (
                <div style={{ marginBottom: 16, padding: 12, background: '#fff7e6', border: '1px solid #ffd591', borderRadius: 4 }}>
                    <Text type="warning">
                        ⚠️ <strong>Demo Data:</strong> This flight is using synthetic/mock data because it was not found in the CSV database. 
                        The information shown may not match actual flight details.
                    </Text>
                </div>
            )}
            <Row gutter={[24, 24]}>
                {/* Route Info */}
                <Col span={12}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                        <div style={{ textAlign: 'left' }}>
                            <Title level={2} style={{ margin: 0 }}>{flight.origin?.icao || 'N/A'}</Title>
                            <Text type="secondary">{flight.origin?.name || flight.origin?.icao || 'Unknown Origin'}</Text>
                        </div>
                        <SendOutlined style={{ fontSize: 24, color: '#bfbfbf', transform: 'rotate(90deg)' }} />
                        <div style={{ textAlign: 'right' }}>
                            <Title level={2} style={{ margin: 0 }}>{flight.destination?.icao || 'N/A'}</Title>
                            <Text type="secondary">{flight.destination?.name || flight.destination?.icao || 'Unknown Destination'}</Text>
                        </div>
                    </div>
                    {flight.airline && (
                        <div style={{ marginTop: 12 }}>
                            <Text strong>Airline: </Text>
                            <Text>{flight.airline.name} ({flight.airline.code})</Text>
                        </div>
                    )}
                    {(flight as any).data_source && (
                        <div style={{ marginTop: 8, fontSize: 12 }}>
                            <Text type="secondary">Data Source: {(flight as any).data_source === 'mock' ? 'Synthetic (Demo)' : 'CSV Database'}</Text>
                        </div>
                    )}
                </Col>

                {/* Time Info */}
                <Col span={12}>
                    <Descriptions column={2}>
                        <Descriptions.Item label="Scheduled Dep">{formatTime(flight.scheduled?.departure)}</Descriptions.Item>
                        <Descriptions.Item label="Actual Dep">{formatTime(flight.actual?.departure)}</Descriptions.Item>
                        <Descriptions.Item label="Scheduled Arr">{formatTime(flight.scheduled?.arrival)}</Descriptions.Item>
                        <Descriptions.Item label="Actual Arr">{formatTime(flight.actual?.arrival)}</Descriptions.Item>
                    </Descriptions>
                    <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                        <ClockCircleOutlined /> {formatDate(flight.scheduled?.departure)}
                    </Text>
                    {flight.departure_delay_minutes !== undefined && flight.departure_delay_minutes !== null && (
                        <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                            Departure Delay: {flight.departure_delay_minutes} min
                        </Text>
                    )}
                    {flight.arrival_delay_minutes !== undefined && flight.arrival_delay_minutes !== null && (
                        <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                            Arrival Delay: {flight.arrival_delay_minutes} min
                        </Text>
                    )}
                    {flight.callsign && (
                        <Text type="secondary" style={{ display: 'block', marginTop: 4 }}>
                            Callsign: <Text code>{flight.callsign}</Text>
                        </Text>
                    )}
                </Col>
            </Row>
        </Card>
    );
}

