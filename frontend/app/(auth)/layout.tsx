import React from 'react';
import { MdOutlineShield } from 'react-icons/md';
import Card from '@/app/components/atoms/Card';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[#FFF8F7] px-4 py-12 sm:px-8">
      <div className="w-full max-w-[460px] space-y-6">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-[16px] bg-[#7E1117] text-white shadow-sm">
            <MdOutlineShield className="text-2xl" />
          </div>
          <h1 className="font-display text-[32px] leading-[40px] tracking-[-0.25px] text-[#251918] sm:text-[40px] sm:leading-[48px] sm:tracking-[-0.5px]">
            Klasifikasi Landslide
          </h1>
          <p className="mt-2 text-sm text-[#58413F]">
            Analisis Bahaya Geospasial &amp; Prioritas Penanganan SAR
          </p>
        </div>

        <Card bgColor="elevated" className="w-full p-8">
          {children}
        </Card>
      </div>
    </main>
  );
}
