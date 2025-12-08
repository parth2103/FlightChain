'use client';

import React, { useEffect, useState } from 'react';
import { Card, Statistic, Row, Col, Progress, Empty } from 'antd';
import { Flight, HistoricalBaseline } from '../types';

interface Props {
    flight: Flight;
}

export default function HistoricalBaselineView({ flight }: Props) {
    const baseline = flight.historicalBaseline;

    if (!baseline) {
        return <Empty description="No historical data available for this route" />;
    }

    const getPerformanceColor = (percent: number) => {
        if (percent >= 80) return '#52c41a';
        if (percent >= 60) return '#faad14';
        return '#f5222d';
    };

    return (
        <div>
            <Row gutter={24} style={{ marginBottom: 24 }}>
                <Col span={8}>
                    <Card size="small">
                        <Statistic
                            title="On-Time Performance"
                            value={baseline.on_time_percentage ?? 0}
                            precision={1}
                            suffix="%"
                            valueStyle={{ 
                                color: baseline.on_time_percentage !== null && baseline.on_time_percentage !== undefined 
                                    ? getPerformanceColor(baseline.on_time_percentage) 
                                    : '#999'
                            }}
                        />
                        {baseline.on_time_percentage !== null && baseline.on_time_percentage !== undefined && (
                            <Progress
                                percent={baseline.on_time_percentage}
                                showInfo={false}
                                strokeColor={getPerformanceColor(baseline.on_time_percentage)}
                                size="small"
                            />
                        )}
                    </Card>
                </Col>
                <Col span={8}>
                    <Card size="small">
                        <Statistic
                            title="Avg Delay"
                            value={baseline.avg_delay_minutes ?? 0}
                            precision={0}
                            suffix="min"
                        />
                        <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                            Typical delay for this route
                        </div>
                    </Card>
                </Col>
                <Col span={8}>
                    <Card size="small">
                        <Statistic
                            title="Total Flights Tracked"
                            value={baseline.total_flights ?? 0}
                        />
                        <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                            Sample size
                        </div>
                    </Card>
                </Col>
            </Row>

            <Card title="Performance Breakdown" size="small">
                <Row gutter={24}>
                    <Col span={12}>
                        <div style={{ textAlign: 'center' }}>
                            <Statistic 
                                title="Avg Departure Delay" 
                                value={baseline.avg_departure_delay ?? 'N/A'} 
                                suffix={baseline.avg_departure_delay !== null && baseline.avg_departure_delay !== undefined ? "min" : ""}
                            />
                        </div>
                    </Col>
                    <Col span={12}>
                        <div style={{ textAlign: 'center' }}>
                            <Statistic 
                                title="Avg Arrival Delay" 
                                value={baseline.avg_arrival_delay ?? baseline.avg_delay_minutes ?? 'N/A'} 
                                suffix={(baseline.avg_arrival_delay !== null && baseline.avg_arrival_delay !== undefined) || 
                                        (baseline.avg_delay_minutes !== null && baseline.avg_delay_minutes !== undefined) ? "min" : ""}
                            />
                        </div>
                    </Col>
                </Row>
            </Card>
        </div>
    );
}
