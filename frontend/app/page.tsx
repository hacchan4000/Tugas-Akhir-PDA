'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Card from '@/app/components/atoms/Card';
import { HistorySection } from '@/app/components/organisms/HistorySection';
import { ModelInfoSection } from '@/app/components/organisms/ModelInfoSection';
import { PredictionDetailModal } from '@/app/components/organisms/PredictionDetailModal';
import { PredictionForm } from '@/app/components/organisms/PredictionForm';
import { PredictionResultCard } from '@/app/components/organisms/PredictionResultCard';
import { TopNavbar, WorkspaceTab } from '@/app/components/organisms/TopNavbar';
import { useAuth } from '@/hooks/useAuth';
import { useHist } from '@/hooks/useHist';
import { formatPercent } from '@/utils/formatters';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { total, latestPrediction, items, modelInfo, health } = useHist();

  const [activeTab, setActiveTab] = useState<WorkspaceTab>('predict');

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.replace('/login');
    }
  }, [authLoading, isAuthenticated, router]);

  if (authLoading || !isAuthenticated) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#FFF8F7] p-8">
        <Card bgColor="elevated" className="w-full max-w-[440px] text-center">
          <p className="text-sm font-bold text-[#251918]">
            {authLoading
              ? 'Memeriksa sesi operator...'
              : 'Mengalihkan ke halaman login...'}
          </p>
        </Card>
      </main>
    );
  }

  const latest = latestPrediction ?? items[0] ?? null;

  return (
    <div className="flex min-h-screen flex-col bg-[#FFF8F7]">
      <TopNavbar activeTab={activeTab} onChangeTab={setActiveTab} />

      <main className="mx-auto w-full max-w-7xl flex-1 space-y-8 px-4 py-8 sm:px-8">
        <section className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <Card bgColor="elevated" className="p-6">
            <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#58413F]">
              Total Riwayat Operator
            </p>
            <p className="font-mono-tabular mt-2 text-3xl font-bold text-[#251918]">
              {total}
            </p>
            <p className="mt-1 text-xs text-[#8B716E]">
              Klasifikasi tersimpan pada akun
            </p>
          </Card>

          <Card bgColor="elevated" className="p-6">
            <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#58413F]">
              Prioritas SAR Terakhir
            </p>
            <p className="font-display mt-2 text-3xl font-normal text-[#7E1117]">
              {latest ? latest.sar_priority_level : '-'}
            </p>
            <p className="mt-1 truncate text-xs text-[#58413F]">
              {latest
                ? `${latest.predicted_class.toUpperCase()} (${formatPercent(latest.confidence_score, 1)})`
                : 'Belum ada klasifikasi'}
            </p>
          </Card>

          <Card bgColor="elevated" className="p-6">
            <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#58413F]">
              Model Aktif
            </p>
            <p className="mt-2 truncate text-xl font-bold text-[#251918]">
              {modelInfo ? `${modelInfo.model_name} (${modelInfo.model_version})` : '-'}
            </p>
            <p className="font-mono-tabular mt-1 text-xs text-[#58413F]">
              {modelInfo?.evaluation_metrics
                ? `Macro-F1: ${formatPercent(modelInfo.evaluation_metrics.macro_f1, 1)}`
                : 'Memuat metadata...'}
            </p>
          </Card>

          <Card bgColor="elevated" className="p-6">
            <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#58413F]">
              Kesiapan Sistem
            </p>
            <p
              className={
                health?.model_ready && health?.database === 'ok'
                  ? 'mt-2 text-xl font-bold text-[#26695E]'
                  : 'mt-2 text-xl font-bold text-[#BA1A1A]'
              }
            >
              {health?.model_ready && health?.database === 'ok'
                ? 'Siap Operasional'
                : health?.status === 'offline'
                  ? 'Backend Offline'
                  : 'Terdegradasi'}
            </p>
            <p className="mt-1 truncate text-xs text-[#58413F]">
              DB: {health?.database ?? '-'} · Model:{' '}
              {health?.model_ready ? 'Ready' : 'Not Ready'}
            </p>
          </Card>
        </section>

        {activeTab === 'predict' && (
          <section className="grid grid-cols-1 gap-6 lg:grid-cols-12">
            <div className="lg:col-span-7">
              <PredictionForm />
            </div>
            <div className="lg:col-span-5">
              <PredictionResultCard />
            </div>
          </section>
        )}

        {activeTab === 'history' && (
          <section>
            <HistorySection />
          </section>
        )}

        {activeTab === 'model' && (
          <section>
            <ModelInfoSection />
          </section>
        )}
      </main>

      <PredictionDetailModal />
    </div>
  );
}
