import type { Metadata } from 'next';
import { AppProvider } from '@/context/AppProvider';
import './globals.css';

export const metadata: Metadata = {
  title: 'Klasifikasi Landslide — Analisis Skala Longsor & Prioritas SAR',
  description:
    'Aplikasi klasifikasi ukuran tanah longsor dan analisis bahaya geospasial untuk dukungan prioritas penanganan SAR.',
};

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="id" className="h-full antialiased">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Baskervville:ital@0;1&family=Lato:wght@400;700&family=Source+Code+Pro:wght@500;600&display=swap"
        />
      </head>
      <body className="min-h-full flex flex-col bg-[#FFF8F7] text-[#251918]">
        <AppProvider>{children}</AppProvider>
      </body>
    </html>
  );
}
