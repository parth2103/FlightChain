'use client';

import React from 'react';
import { ConfigProvider, Layout, theme } from 'antd';
import { AntdRegistry } from '@ant-design/nextjs-registry';
import { usePathname } from 'next/navigation';
import NavigationSidebar from '@/components/NavigationSidebar';

const { Content, Footer } = Layout;

export function AntdProvider({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    // Show sidebar on pages OTHER than landing page
    const showSidebar = pathname !== '/';

    return (
        <AntdRegistry>
            <ConfigProvider
                theme={{
                    algorithm: theme.defaultAlgorithm,
                    token: {
                        colorPrimary: '#1890ff',
                        borderRadius: 8,
                        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji'",
                    },
                    components: {
                        Card: {
                            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                            borderRadius: 12,
                        },
                        Button: {
                            borderRadius: 6,
                            controlHeight: 36,
                        }
                    }
                }}
            >
                <Layout style={{ minHeight: '100vh', height: '100vh', display: 'flex', flexDirection: 'row' }}>
                    {showSidebar && <NavigationSidebar />}

                    <Layout style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
                        <Content style={{
                            flex: 1,
                            overflowY: 'auto',
                            overflowX: 'hidden',
                            display: 'flex',
                            flexDirection: 'column',
                            background: showSidebar ? '#f8f9fa' : '#ffffff'
                        }}>
                            {children}
                            <Footer style={{ textAlign: 'center', flexShrink: 0, background: 'transparent' }}>
                                FlightChain ©{new Date().getFullYear()} - Blockchain Verified Flight Tracking
                            </Footer>
                        </Content>
                    </Layout>
                </Layout>
            </ConfigProvider>
        </AntdRegistry>
    );
}
