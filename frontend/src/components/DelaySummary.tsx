'use client';

import React from 'react';
import { Card, Alert, Typography, Progress, Descriptions } from 'antd';
import { WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { DelayAnalysis } from '../types';

const { Text, Paragraph } = Typography;

interface Props {
    delayAnalysis?: DelayAnalysis;
}

export default function DelaySummary({ delayAnalysis }: Props) {
    if (!delayAnalysis) return null;

    // Determine overall status and color
    const depDelay = delayAnalysis.departure_delay_minutes ?? null;
    const arrDelay = delayAnalysis.arrival_delay_minutes ?? null;

    // Check if delayed, early, or on-time
    const isDelayed = (depDelay !== null && depDelay > 0) || (arrDelay !== null && arrDelay > 0);
    const isEarly = (depDelay !== null && depDelay < 0) || (arrDelay !== null && arrDelay < 0);
    const isOnTime = !isDelayed && !isEarly;

    // Get card background color
    const getCardStyle = () => {
        if (isDelayed) {
            return { marginBottom: 24, height: '100%', backgroundColor: '#fff1f0', borderColor: '#ffccc7' };
        } else if (isEarly) {
            return { marginBottom: 24, height: '100%', backgroundColor: '#f6ffed', borderColor: '#b7eb8f' };
        } else {
            return { marginBottom: 24, height: '100%' };
        }
    };

    const getStatusColor = () => {
        if (isDelayed) return '#f5222d';
        if (isEarly) return '#52c41a';
        return '#52c41a'; // On time is green
    };

    const getStatusText = () => {
        if (isDelayed) {
            const maxDelay = Math.max(depDelay || 0, arrDelay || 0);
            return `${Math.round(maxDelay)} min`;
        } else if (isEarly) {
            const minDelay = Math.min(depDelay || 0, arrDelay || 0);
            return `${Math.round(Math.abs(minDelay))} min early`;
        }
        return 'On Time';
    };

    return (
        <Card
            title="Delay Analysis"
            size="small"
            bordered={false}
            style={getCardStyle()}
        >
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
                <Text strong style={{ fontSize: 24, color: getStatusColor() }}>
                    {getStatusText()}
                </Text>
                <div style={{ marginTop: 4 }}>
                    <Text type="secondary">
                        {isDelayed ? delayAnalysis.category + ' DELAY' :
                            isEarly ? 'EARLY' : 'NONE DELAY'}
                    </Text>
                </div>
            </div>

            {/* Show departure and arrival delays */}
            <Descriptions column={1} size="small" style={{ marginBottom: 16 }}>
                {depDelay !== null && (
                    <Descriptions.Item label="Departure Delay">
                        <Text style={{
                            color: depDelay > 0 ? '#f5222d' : depDelay < 0 ? '#52c41a' : undefined,
                            fontWeight: 'bold'
                        }}>
                            {depDelay > 0 ? '+' : ''}{Math.round(depDelay)} min
                        </Text>
                    </Descriptions.Item>
                )}
                {arrDelay !== null && (
                    <Descriptions.Item label="Arrival Delay">
                        <Text style={{
                            color: arrDelay > 0 ? '#f5222d' : arrDelay < 0 ? '#52c41a' : undefined,
                            fontWeight: 'bold'
                        }}>
                            {arrDelay > 0 ? '+' : ''}{Math.round(arrDelay)} min
                        </Text>
                    </Descriptions.Item>
                )}
            </Descriptions>

            <Alert
                message={isDelayed ? "Delay Explanation" : "On Time Performance"}
                description={delayAnalysis.human_readable}
                type={isDelayed ? "warning" : "success"}
                showIcon
                icon={isDelayed ? <WarningOutlined /> : <CheckCircleOutlined />}
                style={{ marginBottom: 16 }}
            />

            {delayAnalysis.reasons.length > 0 && (
                <div>
                    <Text strong>Delay Breakdown:</Text>
                    {delayAnalysis.reasons.map((reason, idx) => (
                        <div key={idx} style={{ marginTop: 8 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <Text type="secondary">{reason.type.replace('_', ' ')}</Text>
                                <Text>{Math.round(reason.minutes)} min</Text>
                            </div>
                            <Progress
                                percent={Math.min(100, Math.round((reason.minutes / delayAnalysis.total_delay_minutes) * 100))}
                                size="small"
                                status="exception"
                                showInfo={false}
                            />
                        </div>
                    ))}
                </div>
            )}
        </Card>
    );
}
