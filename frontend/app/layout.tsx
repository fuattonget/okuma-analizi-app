import './globals.css';
import { Inter } from 'next/font/google';
import KeyboardShortcuts from '@/components/KeyboardShortcuts';
import { ThemeProvider } from '@/components/ThemeProvider';
import GlobalActivityTracker from '@/components/GlobalActivityTracker';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'Doky',
  description: 'Reading analysis application',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className={inter.className}>
        <ThemeProvider>
          <GlobalActivityTracker />
          {children}
          <KeyboardShortcuts global={true} />
        </ThemeProvider>
      </body>
    </html>
  );
}