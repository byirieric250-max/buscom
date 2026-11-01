import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Imena — Rwanda, made local',
  description: 'Discover local businesses, shop their products, and book the things you love across Rwanda.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
