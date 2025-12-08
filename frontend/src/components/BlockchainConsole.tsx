import React, { useEffect, useState, useRef } from 'react';
import { Card, Typography, Space, Tag } from 'antd';
import { ConsoleSqlOutlined, LoadingOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';

interface LogEntry {
    type: 'info' | 'success' | 'warning' | 'error' | 'data';
    message: string;
    details?: any;
}

interface BlockchainConsoleProps {
    logs: LogEntry[];
    visible: boolean;
    onComplete?: () => void;
}

export default function BlockchainConsole({ logs, visible, onComplete }: BlockchainConsoleProps) {
    const [displayedLogs, setDisplayedLogs] = useState<LogEntry[]>([]);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (visible && logs.length > 0) {
            setDisplayedLogs([]); // Reset on new visible session

            // Filter out invalid logs before displaying
            const validLogs = logs.filter(log => log && log.type && log.message);

            if (validLogs.length === 0) {
                return;
            }

            let i = 0;
            const interval = setInterval(() => {
                if (i < validLogs.length) {
                    setDisplayedLogs(prev => [...prev, validLogs[i]]);
                    i++;
                } else {
                    clearInterval(interval);
                    if (onComplete) setTimeout(onComplete, 1000); // Wait a second after logs finish
                }
            }, 800); // 800ms delay between log lines for "typing" effect

            return () => clearInterval(interval);
        }
    }, [visible, logs, onComplete]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [displayedLogs]);

    if (!visible) return null;

    return (
        <Card
            title={<Space><ConsoleSqlOutlined /> Blockchain Trace Console</Space>}
            style={{
                background: '#1e1e1e',
                color: '#d4d4d4',
                border: '1px solid #333',
                marginBottom: 24,
                fontFamily: 'monospace'
            }}
            headStyle={{ color: '#fff', borderBottom: '1px solid #333' }}
            bodyStyle={{ padding: '12px 16px', maxHeight: '300px', overflowY: 'auto' }}
        >
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {displayedLogs
                    .filter((log) => log && log.type && log.message) // Filter out invalid logs
                    .map((log, idx) => (
                    <div key={idx} style={{ opacity: 0, animation: 'fadeIn 0.3s forwards' }}>
                        <Space align="start">
                            <span style={{ color: '#569cd6' }}>{'>'}</span>
                            {log.type === 'info' && <span style={{ color: '#9cdcfe' }}>[INFO]</span>}
                            {log.type === 'success' && <span style={{ color: '#4ec9b0' }}>[SUCCESS]</span>}
                            {log.type === 'warning' && <span style={{ color: '#ce9178' }}>[WARN]</span>}
                            {log.type === 'error' && <span style={{ color: '#f44747' }}>[ERROR]</span>}
                            {log.type === 'data' && <span style={{ color: '#dcdcaa' }}>[DATA]</span>}
                            {!['info', 'success', 'warning', 'error', 'data'].includes(log.type) && (
                                <span style={{ color: '#808080' }}>[LOG]</span>
                            )}

                            <span>{log.message || 'No message'}</span>
                        </Space>
                        {log.details && (
                            <div style={{ paddingLeft: 24, fontSize: '0.9em', color: '#6a9955', marginTop: 4 }}>
                                {JSON.stringify(log.details, null, 2)}
                            </div>
                        )}
                    </div>
                ))}
                {displayedLogs.length < logs.length && (
                    <div style={{ paddingLeft: 12, color: '#808080' }}>
                        <Space>
                            <LoadingOutlined />
                            <span>Processing...</span>
                        </Space>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>
            <style jsx global>{`
        @keyframes fadeIn {
          to { opacity: 1; }
        }
      `}</style>
        </Card>
    );
}
