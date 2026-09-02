import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'OIL SENTINEL - SIF Precursor Intelligence Engine',
  description: 'AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors in Safety Reports',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased bg-industrial-950 text-industrial-100">
        {children}
      </body>
    </html>
  );
}
