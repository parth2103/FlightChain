'use client';

import React from 'react';
import { Table, Tag, Typography, Tooltip } from 'antd';
import { CheckCircleOutlined, SafetyCertificateOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { BlockchainEvent } from '../types';

const { Text } = Typography;

interface Props {
    events?: BlockchainEvent[];
}

export default function BlockchainLog({ events }: Props) {
    const columns = [
        {
            title: 'Event Type',
            dataIndex: 'event_type',
            key: 'event_type',
            render: (text: string) => <Tag color="blue">{text}</Tag>,
        },
        {
            title: 'Timestamp',
            dataIndex: 'timestamp',
            key: 'timestamp',
            render: (text: string) => dayjs(text).format('YYYY-MM-DD HH:mm:ss'),
            responsive: ['md'] as any,
        },
        {
            title: 'Block',
            dataIndex: 'block_number',
            key: 'block_number',
            render: (text: number) => <Tag color="purple">#{text}</Tag>,
        },
        {
            title: 'Data Hash',
            dataIndex: 'data_hash',
            key: 'data_hash',
            render: (text: string) => (
                <Tooltip title={text}>
                    <Text code style={{ fontSize: 12 }}>
                        {text.substring(0, 10)}...{text.substring(text.length - 8)}
                    </Text>
                </Tooltip>
            ),
        },
        {
            title: 'Tx Hash',
            dataIndex: 'tx_hash',
            key: 'tx_hash',
            render: (text: string) => (
                <Tooltip title={text}>
                    <a href="#" onClick={(e) => e.preventDefault()}>
                        <Text code style={{ color: '#1890ff', fontSize: 12 }}>
                            {text.substring(0, 10)}...
                        </Text>
                    </a>
                </Tooltip>
            ),
        },
        {
            title: 'Status',
            key: 'status',
            render: () => (
                <Tag icon={<CheckCircleOutlined />} color="success">
                    Verified
                </Tag>
            ),
        },
    ];

    if (!events || events.length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: 40 }}>
                <SafetyCertificateOutlined style={{ fontSize: 40, color: '#d9d9d9' }} />
                <p style={{ color: '#999', marginTop: 16 }}>No blockchain records found for this flight.</p>
                <p style={{ color: '#666', marginTop: 8, fontSize: 12 }}>
                    Events exist in the database but haven't been recorded on the blockchain yet.
                    <br />
                    Use the button below to record events on-chain via MetaMask.
                </p>
            </div>
        );
    }

    return (
        <Table
            columns={columns}
            dataSource={events}
            rowKey={(record) => record.tx_hash}
            pagination={false}
            size="small"
        />
    );
}
