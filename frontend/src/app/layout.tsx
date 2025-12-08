import React from 'react';
import '../styles/globals.css';
import { AntdProvider } from '../lib/AntdProvider';
import { Layout } from 'antd'; // Import Layout types only if needed or just use div structure for the server part if feasible, but AntdProvider handles the Antd Layout component now.

// Actually AntdProvider wraps the Antd Layout, but we need the Header/Footer content structure.
// Let's redefine the specific layout structure inside the Provider or pass it as children?
// For simplicity, let's keep the Layout *structure* in the Provider, and just render children.
// But wait, the original layout had Header/Footer with content.
// I should move the *entire* shell into the client component or compose it.
// Let's update AntdProvider to include the Header/Footer shell to be safe.

export const metadata = {
    title: 'FlightChain',
    description: 'Blockchain Verified Flight Tracking',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body>
                <AntdProvider>
                    {/* The shell structure is now inside AntdProvider? No, let's check the file I just wrote. 
                 I wrote a wrapper that renders <Layout>{children}</Layout>.
                 I need to restore the Header/Content/Footer structure.
                 I will update AntdProvider in the NEXT step to include the full shell, 
                 or I should have done it in the previous step.
                 
                 Actually, simpler: simpler allow AntdProvider to just provide config, 
                 and put the Layout components inside it? 
                 But Layout is a property of 'antd' which is causing the import error. 
                 So YES, all 'antd' components should be in the client file.
             */}
                    {children}
                </AntdProvider>
            </body>
        </html>
    );
}
