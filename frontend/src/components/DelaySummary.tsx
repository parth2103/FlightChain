'use client';

import React from 'react';
import { Card, Alert, Typography, Progress } from 'antd';
import { WarningOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { DelayAnalysis } from '../types';

const { Text, Paragraph } = Typography;

interface Props {
    delayAnalysis?: DelayAnalysis;
}

export default function DelaySummary({ delayAnalysis }: Props) {
    if (!delayAnalysis) return null;

    const getStatusColor = () => {
        switch (delayAnalysis.category) {
            case 'NONE': return '#52c41a';
            case 'MINOR': return '#1890ff';
            case 'MODERATE': return '#faad14';
            default: return '#f5222d';
        }
    };

    return (
        <Card
            title="Delay Analysis"
            size="small"
            style={{ marginBottom: 24, height: '100%' }}
        >
            <div style={{ textAlign: 'center', marginBottom: 16 }}>
                <Text strong style={{ fontSize: 24, color: getStatusColor() }}>
                    {delayAnalysis.total_delay_minutes > 0
                        ? `${Math.round(delayAnalysis.total_delay_minutes)} min`
                        : 'On Time'}
                </Text>
                <div style={{ marginTop: 4 }}>
                    <Text type="secondary">{delayAnalysis.category} DELAY</Text>
                </div>
            </div>

            <Alert
                message={delayAnalysis.is_delayed ? "Delay Explanation" : "On Time Performance"}
                description={delayAnalysis.human_readable}
                type={delayAnalysis.is_delayed ? "warning" : "success"}
                showIcon
                icon={delayAnalysis.is_delayed ? <WarningOutlined /> : <CheckCircleOutlined />}
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
