'use client';

import React from 'react';
import { ConfigProvider, Layout, theme } from 'antd';
import { AntdRegistry } from '@ant-design/nextjs-registry';

const { Content, Footer } = Layout;

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
                <Layout style={{ minHeight: '100vh', height: '100vh', display: 'flex', flexDirection: 'column' }}>
                    <Content style={{ padding: '0', flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
                        {children}
                    </Content>

                    <Footer style={{ textAlign: 'center', flexShrink: 0 }}>
                        FlightChain ©{new Date().getFullYear()} - Blockchain Verified Flight Tracking
                    </Footer>
                </Layout>
            </ConfigProvider>
        </AntdRegistry>
    );
}
