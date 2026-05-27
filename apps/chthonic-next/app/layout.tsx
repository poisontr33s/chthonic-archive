import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Chthonic Next Lane',
  description: 'Bun-native Next.js cockpit lane for Chthonic Archive',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-obsidian bg-sediment font-display text-chalk">
        <div className="grid-overlay min-h-screen">{children}</div>
      </body>
    </html>
  );
}
