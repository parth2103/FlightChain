'use client';

import React, { useState } from 'react';
import { Layout, Menu, Button } from 'antd';
import { HomeOutlined, RocketOutlined, MenuUnfoldOutlined, MenuFoldOutlined, BlockOutlined, LineChartOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import Image from 'next/image';

const { Sider } = Layout;

export default function NavigationSidebar() {
    const router = useRouter();
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const [collapsed, setCollapsed] = useState(false);

    // Determine selected key based on pathname and query
    const getSelectedKey = () => {
        if (pathname === '/') return '1';
        if (pathname.startsWith('/flight/')) {
            const view = searchParams.get('view');
            if (view === 'timeline') return '3';
            if (view === 'blockchain') return '4';
            if (view === 'baseline') return '5';
            return '2';
        }
        return '';
    };

    return (
        <Sider
            trigger={null}
            collapsible
            collapsed={collapsed}
            width={240}
            theme="light"
            style={{
                boxShadow: '2px 0 8px rgba(0,0,0,0.05)',
                zIndex: 10,
                borderRight: '1px solid #f0f0f0'
            }}
        >
            <div style={{
                height: 64,
                display: 'flex',
                alignItems: 'center',
                justifyContent: collapsed ? 'center' : 'space-between',
                padding: collapsed ? '0' : '0 24px',
                borderBottom: '1px solid #f0f0f0'
            }}>
                {!collapsed ? (
                    <div style={{ display: 'flex', alignItems: 'center', paddingLeft: 8 }}>
                        <Image src="/logo.png" alt="FlightChain" width={140} height={40} style={{ objectFit: 'contain' }} />
                    </div>
                ) : (
                    <RocketOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                )}

                <Button
                    type="text"
                    icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                    onClick={() => setCollapsed(!collapsed)}
                    style={{ marginLeft: collapsed ? 0 : 8 }}
                />
            </div>

            <Menu
                mode="inline"
                selectedKeys={[getSelectedKey()]}
                style={{ borderRight: 0, marginTop: 16 }}
                items={[
                    {
                        key: '1',
                        icon: <HomeOutlined />,
                        label: 'Home',
                        onClick: () => router.push('/'),
                    },
                    {
                        key: '2',
                        icon: <RocketOutlined />,
                        label: 'Flight Overview',
                        disabled: !pathname.startsWith('/flight/'),
                        onClick: () => {
                            if (pathname.startsWith('/flight/')) {
                                // Keep the current flight ID but remove query params
                                const flightId = pathname.split('/')[2];
                                router.push(`/flight/${flightId}`);
                            }
                        },
                    },
                    ...(pathname.startsWith('/flight/') ? [
                        {
                            key: '3',
                            icon: <ClockCircleOutlined />,
                            label: 'Event Timeline',
                            onClick: () => {
                                const flightId = pathname.split('/')[2];
                                router.push(`/flight/${flightId}?view=timeline`);
                            },
                        },
                        {
                            key: '4',
                            icon: <BlockOutlined />,
                            label: 'Blockchain Log',
                            onClick: () => {
                                const flightId = pathname.split('/')[2];
                                router.push(`/flight/${flightId}?view=blockchain`);
                            },
                        },
                        {
                            key: '5',
                            icon: <LineChartOutlined />,
                            label: 'Historical Baseline',
                            onClick: () => {
                                const flightId = pathname.split('/')[2];
                                router.push(`/flight/${flightId}?view=baseline`);
                            },
                        }
                    ] : [])
                ]}
            />
        </Sider>
    );
}

