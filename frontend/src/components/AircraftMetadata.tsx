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
            title={<><RocketOutlined /> Aircraft Information</>}
            size="small"
            style={{ marginBottom: 24, height: '100%' }}
        >
            <Descriptions column={1} size="small">
                <Descriptions.Item label="Registration">
                    <Tag>{aircraft.registration || 'N/A'}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Type">
                    {aircraft.manufacturer} {aircraft.model}
                </Descriptions.Item>
                <Descriptions.Item label="Type Code">{aircraft.type_code}</Descriptions.Item>
                <Descriptions.Item label="Age">
                    {aircraft.age_years ? `${aircraft.age_years} years` : 'Unknown'}
                </Descriptions.Item>
                <Descriptions.Item label="ICAO24">
                    <span style={{ fontFamily: 'monospace' }}>{aircraft.icao24}</span>
                </Descriptions.Item>
            </Descriptions>
        </Card>
    );
}
