'use client';

import React from 'react';
import { ConfigProvider, Layout, theme } from 'antd';
import { AntdRegistry } from '@ant-design/nextjs-registry';

const { Header, Content, Footer } = Layout;

export function AntdProvider({ children }: { children: React.ReactNode }) {
    return (
        <AntdRegistry>
            <ConfigProvider
                theme={{
                    algorithm: theme.defaultAlgorithm,
                    token: {
                        colorPrimary: '#1890ff',
                        borderRadius: 4,
                    },
                }}
            >
                <Layout style={{ minHeight: '100vh' }}>
                    <Header
                        style={{
                            display: 'flex',
                            alignItems: 'center',
                            background: '#001529',
                            padding: '0 24px',
                        }}
                    >
                        <div
                            className="logo"
                            style={{
                                color: 'white',
                                fontSize: '20px',
                                fontWeight: 600,
                                marginRight: '24px'
                            }}
                        >
                            FlightChain
                        </div>
                    </Header>

                    <Content style={{ padding: '24px 48px', minHeight: 280 }}>
                        {children}
                    </Content>

                    <Footer style={{ textAlign: 'center' }}>
                        FlightChain ©{new Date().getFullYear()} - Blockchain Verified Flight Tracking
                    </Footer>
                </Layout>
            </ConfigProvider>
        </AntdRegistry>
    );
}
