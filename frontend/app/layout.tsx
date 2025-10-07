import './globals.css';
import { Inter } from 'next/font/google';
import KeyboardShortcuts from '@/components/KeyboardShortcuts';
import { ThemeProvider } from '@/components/ThemeProvider';

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
          {children}
          <KeyboardShortcuts global={true} />
        </ThemeProvider>
      </body>
    </html>
  );
}