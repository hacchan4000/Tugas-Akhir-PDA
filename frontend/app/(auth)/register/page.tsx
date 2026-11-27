'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Button from '@/app/components/atoms/Button';

export default function RegisterInfoPage() {
  const router = useRouter();

  return (
    <div className="space-y-5 text-center">
      <div className="space-y-2">
        <h2 className="font-display text-[28px] leading-[36px] text-[#251918]">
          Akses Akun Operator
        </h2>
        <p className="text-sm leading-relaxed text-[#58413F]">
          Pendaftaran publik dinonaktifkan untuk menjaga integritas operasional.
          Akun operator dibuat oleh administrator melalui skrip backend{' '}
          <code className="font-mono-tabular rounded bg-[#FFF0EF] px-1.5 py-0.5 text-xs text-[#7E1117]">
            scripts.seed_operator
          </code>
          .
        </p>
      </div>

      <Button
        label="Log in here"
        variant="contained"
        color="primary"
        fullWidth
        className="h-12"
        onClick={() => router.push('/login')}
      />
    </div>
  );
}
