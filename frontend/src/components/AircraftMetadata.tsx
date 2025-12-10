'use client';

import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { RocketOutlined } from '@ant-design/icons';
import { Aircraft } from '../types';

interface Props {
    aircraft?: Aircraft;
}

export default function AircraftMetadata({ aircraft }: Props) {
    if (!aircraft) return null;

    return (
        <Card
            title={<><RocketOutlined style={{ fontSize: '20px', marginRight: 8 }} /> <span style={{ fontSize: '18px' }}>Aircraft Information</span></>}
            bordered={false}
            style={{ marginBottom: 24, height: '100%' }}
        >
            <Descriptions
                column={1}
                labelStyle={{ fontSize: '16px', color: '#666' }}
                contentStyle={{ fontSize: '16px', fontWeight: 500 }}
            >
                <Descriptions.Item label="Registration">
                    <Tag style={{ fontSize: '14px', padding: '4px 10px' }}>{aircraft.registration || 'N/A'}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Type">
                    {aircraft.manufacturer} {aircraft.model}
                </Descriptions.Item>
                <Descriptions.Item label="Type Code">{aircraft.type_code}</Descriptions.Item>
                <Descriptions.Item label="Age">
                    {aircraft.age_years ? `${aircraft.age_years} years` : 'Unknown'}
                </Descriptions.Item>
                <Descriptions.Item label="ICAO24">
                    <span style={{ fontFamily: 'monospace', background: '#f5f5f5', padding: '2px 6px', borderRadius: 4 }}>{aircraft.icao24}</span>
                </Descriptions.Item>
            </Descriptions>
        </Card>
    );
}
