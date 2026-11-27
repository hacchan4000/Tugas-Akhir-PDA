'use client';

import React from 'react';
import { MdClose, MdLocationOn } from 'react-icons/md';
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

export function PredictionDetailModal() {
  const { selectedPrediction, detailLoading, closeDetail } = useHist();

  if (!selectedPrediction && !detailLoading) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#251918]/45 p-4 backdrop-blur-xs"
      role="dialog"
      aria-modal="true"
    >
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[24px] border border-[#DFBFBC] bg-white p-8 shadow-[0_16px_40px_-12px_rgba(37,25,24,0.18)]">
        <div className="flex items-start justify-between gap-4 border-b border-[#DFBFBC] pb-4">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#8B716E]">
              Detail Riwayat Klasifikasi
            </p>
            <h3 className="font-display mt-1 text-2xl font-normal text-[#251918]">
              {selectedPrediction ? `Laporan #${selectedPrediction.prediction_id}` : 'Memuat...'}
            </h3>
          </div>
          <button
            type="button"
            onClick={closeDetail}
            className="rounded-[10px] border border-transparent p-1.5 text-[#58413F] transition duration-150 hover:border-[#DFBFBC] hover:bg-[#FFF0EF] hover:text-[#251918] cursor-pointer"
            aria-label="Tutup modal detail"
          >
            <MdClose className="text-xl" />
          </button>
        </div>

        {detailLoading || !selectedPrediction ? (
          <div className="py-12 text-center text-sm text-[#58413F]">
            Mengambil detail klasifikasi...
          </div>
        ) : (
          <div className="mt-5 space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <PredictedClassBadge predictedClass={selectedPrediction.predicted_class} />
                <SarPriorityBadge
                  predictedClass={selectedPrediction.predicted_class}
                  level={selectedPrediction.sar_priority_level}
                />
              </div>
              <span className="font-mono-tabular text-sm font-bold text-[#7E1117]">
                Confidence: {formatPercent(selectedPrediction.confidence_score, 2)}
              </span>
            </div>

            <div className="rounded-[16px] border border-[#DFBFBC] bg-[#FFF0EF] p-4">
              <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#7E1117]">
                Rekomendasi Penanganan SAR
              </p>
              <p className="mt-1 text-sm leading-relaxed text-[#251918]">
                {selectedPrediction.sar_recommendation}
              </p>
            </div>

            <div>
              <p className="mb-2.5 text-xs font-bold uppercase tracking-[0.25px] text-[#58413F]">
                Probabilitas per Kelas
              </p>
              <ProbabilityBars probabilities={selectedPrediction.probabilities} />
            </div>

            <div className="grid grid-cols-1 gap-4 rounded-[16px] border border-[#DFBFBC] bg-[#FFF8F7] p-4 text-xs sm:grid-cols-2">
              <div>
                <span className="text-[#8B716E]">Tanggal Kejadian</span>
                <p className="mt-0.5 font-bold text-[#251918]">
                  {formatDateID(selectedPrediction.event_date)}
                </p>
              </div>
              <div>
                <span className="text-[#8B716E]">Waktu Prediksi</span>
                <p className="mt-0.5 font-bold text-[#251918]">
                  {formatDateTimeID(selectedPrediction.prediction_date)}
                </p>
              </div>
              <div className="sm:col-span-2">
                <span className="text-[#8B716E]">Lokasi (Reverse Geocoding)</span>
                <p className="mt-0.5 flex items-center gap-1.5 font-bold text-[#251918]">
                  <MdLocationOn className="text-base text-[#26695E]" />
                  <span>
                    {selectedPrediction.nama_wilayah || 'Tidak tersedia'} (
                    <span className="font-mono-tabular">
                      {selectedPrediction.latitude.toFixed(6)},{' '}
                      {selectedPrediction.longitude.toFixed(6)}
                    </span>{' '}
                    · {selectedPrediction.geocoding_status})
                  </span>
                </p>
              </div>
              <div>
                <span className="text-[#8B716E]">Kategori Longsor</span>
                <p className="mt-0.5 font-bold text-[#251918]">
                  {formatCategoryLabel(selectedPrediction.landslide_category)}
                </p>
              </div>
              <div>
                <span className="text-[#8B716E]">Pemicu Longsor</span>
                <p className="mt-0.5 font-bold text-[#251918]">
                  {formatCategoryLabel(selectedPrediction.landslide_trigger)}
                </p>
              </div>
              <div>
                <span className="text-[#8B716E]">Kondisi Lingkungan</span>
                <p className="mt-0.5 font-bold text-[#251918]">
                  {formatCategoryLabel(selectedPrediction.landslide_setting)}
                </p>
              </div>
              <div>
                <span className="text-[#8B716E]">Akurasi Lokasi</span>
                <p className="mt-0.5 font-bold text-[#251918]">
                  {formatCategoryLabel(selectedPrediction.location_accuracy)}
                </p>
              </div>
              <div className="sm:col-span-2">
                <span className="text-[#8B716E]">Model &amp; Status</span>
                <p className="font-mono-tabular mt-0.5 font-bold text-[#251918]">
                  {selectedPrediction.model_name} ({selectedPrediction.model_version}) ·{' '}
                  {selectedPrediction.status}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
