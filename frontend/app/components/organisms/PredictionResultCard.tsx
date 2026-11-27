'use client';

import React from 'react';
import { MdLocationOn, MdOutlineTipsAndUpdates, MdRadar } from 'react-icons/md';
import Card from '@/app/components/atoms/Card';
import {
  PredictedClassBadge,
  SarPriorityBadge,
} from '@/app/components/molecules/ClassBadge';
import { ProbabilityBars } from '@/app/components/molecules/ProbabilityBars';
import { useHist } from '@/hooks/useHist';
import {
  formatCategoryLabel,
  formatDateID,
  formatDateTimeID,
  formatPercent,
} from '@/utils/formatters';

export function PredictionResultCard() {
  const { latestPrediction, items } = useHist();
  const displayItem = latestPrediction ?? items[0] ?? null;

  if (!displayItem) {
    return (
      <Card bgColor="elevated" className="flex h-full flex-col justify-center">
        <div className="mx-auto max-w-sm space-y-3 py-8 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-[16px] bg-[#FFF0EF] text-[#7E1117] border border-[#DFBFBC]">
            <MdRadar className="text-2xl" />
          </div>
          <h3 className="font-display text-xl font-normal text-[#251918]">
            Belum Ada Hasil Klasifikasi
          </h3>
          <p className="text-sm leading-relaxed text-[#58413F]">
            Lengkapi parameter kejadian tanah longsor lalu pilih{' '}
            <span className="font-bold text-[#7E1117]">Klasifikasikan Kejadian</span>{' '}
            untuk melihat estimasi skala serta rekomendasi prioritas penanganan SAR.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card bgColor="elevated" className="flex h-full flex-col justify-between gap-6">
      <div className="space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-2 border-b border-[#DFBFBC]/60 pb-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#8B716E]">
              {latestPrediction ? 'Hasil Klasifikasi Terbaru' : 'Klasifikasi Terakhir'}
            </p>
            <h3 className="font-mono-tabular mt-1 text-lg font-bold text-[#251918]">
              Laporan #{displayItem.prediction_id}
            </h3>
          </div>
          <SarPriorityBadge
            predictedClass={displayItem.predicted_class}
            level={displayItem.sar_priority_level}
          />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 rounded-[16px] border border-[#DFBFBC] bg-[#FFF8F7] p-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2px] text-[#58413F]">
              Skala Terprediksi
            </p>
            <div className="mt-2">
              <PredictedClassBadge predictedClass={displayItem.predicted_class} />
            </div>
          </div>
          <div className="text-right">
            <p className="text-xs font-bold uppercase tracking-[0.2px] text-[#58413F]">
              Confidence Score
            </p>
            <p className="font-mono-tabular mt-1 text-2xl font-bold text-[#7E1117]">
              {formatPercent(displayItem.confidence_score, 1)}
            </p>
          </div>
        </div>

        <div className="rounded-[16px] border border-[#DFBFBC] bg-[#FFF0EF] p-4">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.25px] text-[#7E1117]">
            <MdOutlineTipsAndUpdates className="text-base" />
            Rekomendasi Penanganan SAR
          </div>
          <p className="mt-1.5 text-sm leading-relaxed text-[#251918]">
            {displayItem.sar_recommendation}
          </p>
        </div>

        <div>
          <p className="mb-3 text-xs font-bold uppercase tracking-[0.25px] text-[#58413F]">
            Distribusi Probabilitas Kelas
          </p>
          <ProbabilityBars probabilities={displayItem.probabilities} />
        </div>
      </div>

      <div className="space-y-2 border-t border-[#DFBFBC] pt-4 text-xs text-[#58413F]">
        <div className="flex items-start gap-2">
          <MdLocationOn className="mt-0.5 shrink-0 text-base text-[#26695E]" />
          <div>
            <p className="font-bold text-[#251918]">
              {displayItem.nama_wilayah || 'Wilayah tidak teridentifikasi'}
            </p>
            <p className="font-mono-tabular text-[12px] text-[#58413F]">
              {displayItem.latitude.toFixed(5)}, {displayItem.longitude.toFixed(5)} · Geocoding:{' '}
              {displayItem.geocoding_status}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap justify-between gap-2 text-[12px] text-[#8B716E]">
          <span>
            Kejadian: {formatDateID(displayItem.event_date)} ·{' '}
            {formatCategoryLabel(displayItem.landslide_category)}
          </span>
          <span className="font-mono-tabular">
            {displayItem.model_name} ({displayItem.model_version}) ·{' '}
            {formatDateTimeID(displayItem.prediction_date)}
          </span>
        </div>
      </div>
    </Card>
  );
}
