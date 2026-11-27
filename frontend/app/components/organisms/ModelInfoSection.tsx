'use client';

import React from 'react';
import Card from '@/app/components/atoms/Card';
import { useHist } from '@/hooks/useHist';
import { formatDateTimeID, formatPercent } from '@/utils/formatters';

export function ModelInfoSection() {
  const { modelInfo, loadingMeta } = useHist();

  if (loadingMeta && !modelInfo) {
    return (
      <Card bgColor="elevated">
        <p className="py-10 text-center text-sm text-[#58413F]">
          Memuat metadata model aktif...
        </p>
      </Card>
    );
  }

  if (!modelInfo) {
    return (
      <Card bgColor="elevated">
        <p className="py-10 text-center text-sm text-[#58413F]">
          Informasi model belum tersedia. Pastikan artefak model aktif di backend.
        </p>
      </Card>
    );
  }

  const metrics = modelInfo.evaluation_metrics;
  const cmLabels = metrics?.labels ?? modelInfo.class_labels;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card bgColor="elevated" className="lg:col-span-2">
          <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#7E1117]">
            Model Produksi Aktif
          </p>
          <div className="mt-2 flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="font-display text-[28px] font-normal text-[#251918]">
              {modelInfo.model_name}
            </h2>
            <span className="rounded-full border border-[#26695E]/30 bg-[#ABECDE]/60 px-3 py-1 text-xs font-bold text-[#26695E]">
              Versi {modelInfo.model_version}
            </span>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-4 text-xs sm:grid-cols-4">
            <div className="rounded-[12px] border border-[#DFBFBC] bg-[#FFF8F7] p-3.5">
              <p className="text-[#58413F]">Dimensi Fitur (d_enc)</p>
              <p className="font-mono-tabular mt-1 text-lg font-bold text-[#251918]">
                {modelInfo.d_enc}
              </p>
            </div>
            <div className="rounded-[12px] border border-[#DFBFBC] bg-[#FFF8F7] p-3.5">
              <p className="text-[#58413F]">Jumlah Kelas</p>
              <p className="font-mono-tabular mt-1 text-lg font-bold text-[#251918]">
                {modelInfo.class_labels.length}
              </p>
            </div>
            <div className="col-span-2 rounded-[12px] border border-[#DFBFBC] bg-[#FFF8F7] p-3.5">
              <p className="text-[#58413F]">Tanggal Pelatihan</p>
              <p className="mt-1 text-sm font-bold text-[#251918]">
                {formatDateTimeID(modelInfo.trained_date)}
              </p>
            </div>
          </div>

          <div className="mt-5">
            <p className="mb-2 text-xs font-bold uppercase tracking-[0.25px] text-[#58413F]">
              Hyperparameter Terbaik
            </p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(modelInfo.best_params).map(([key, val]) => (
                <span
                  key={key}
                  className="font-mono-tabular rounded-[10px] border border-[#DFBFBC] bg-[#FFF0EF] px-3 py-1.5 text-xs font-medium text-[#251918]"
                >
                  {key}: {val === null ? 'null' : String(val)}
                </span>
              ))}
            </div>
          </div>
        </Card>

        <Card bgColor="elevated">
          <p className="text-xs font-bold uppercase tracking-[0.25px] text-[#26695E]">
            Model Pembanding
          </p>
          {modelInfo.comparator_info ? (
            <div className="mt-2 space-y-4">
              <h3 className="font-display text-2xl font-normal text-[#251918]">
                {modelInfo.comparator_info.model_name}
              </h3>
              {modelInfo.comparator_info.mean_test_macro_f1 !== undefined && (
                <div className="rounded-[12px] border border-[#DFBFBC] bg-[#FFF8F7] p-3.5">
                  <p className="text-xs text-[#58413F]">Mean Test Macro-F1</p>
                  <p className="font-mono-tabular mt-1 text-xl font-bold text-[#26695E]">
                    {formatPercent(modelInfo.comparator_info.mean_test_macro_f1, 2)}
                  </p>
                </div>
              )}
              {modelInfo.comparator_info.best_params && (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(modelInfo.comparator_info.best_params).map(
                    ([k, v]) => (
                      <span
                        key={k}
                        className="font-mono-tabular rounded-[8px] border border-[#DFBFBC] bg-[#FFF0EF] px-2.5 py-1 text-xs text-[#251918]"
                      >
                        {k}: {String(v)}
                      </span>
                    )
                  )}
                </div>
              )}
            </div>
          ) : (
            <p className="mt-3 text-sm text-[#58413F]">
              Tidak ada metadata pembanding.
            </p>
          )}
        </Card>
      </div>

      {metrics && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Card bgColor="elevated" className="space-y-5">
            <h3 className="font-display text-xl font-normal text-[#251918]">
              Metrik Evaluasi Holdout
            </h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <div className="rounded-[12px] border border-[#DFBFBC] bg-[#FFF0EF] p-3.5">
                <p className="text-xs font-bold text-[#58413F]">Macro-F1</p>
                <p className="font-mono-tabular mt-1 text-lg font-bold text-[#7E1117]">
                  {formatPercent(metrics.macro_f1, 2)}
                </p>
              </div>
              <div className="rounded-[12px] border border-[#DFBFBC] bg-[#FFF8F7] p-3.5">
                <p className="text-xs font-bold text-[#58413F]">Balanced Accuracy</p>
                <p className="font-mono-tabular mt-1 text-lg font-bold text-[#00464E]">
                  {formatPercent(metrics.balanced_accuracy, 2)}
                </p>
              </div>
              <div className="rounded-[12px] border border-[#DFBFBC] bg-[#FFF8F7] p-3.5">
                <p className="text-xs font-bold text-[#58413F]">Accuracy</p>
                <p className="font-mono-tabular mt-1 text-lg font-bold text-[#26695E]">
                  {formatPercent(metrics.accuracy, 2)}
                </p>
              </div>
            </div>

            <div className="overflow-x-auto rounded-[14px] border border-[#DFBFBC]">
              <table className="min-w-full divide-y divide-[#DFBFBC] text-left text-xs">
                <thead className="bg-[#FFF0EF] font-bold uppercase text-[#58413F]">
                  <tr>
                    <th className="px-3.5 py-2.5">Kelas</th>
                    <th className="px-3.5 py-2.5">Precision</th>
                    <th className="px-3.5 py-2.5">Recall</th>
                    <th className="px-3.5 py-2.5">F1-Score</th>
                    <th className="px-3.5 py-2.5 text-right">Support</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#DFBFBC]/70 bg-white">
                  {Object.entries(metrics.per_class).map(([cls, row]) => (
                    <tr key={cls}>
                      <td className="px-3.5 py-2.5 font-bold uppercase text-[#251918]">
                        {cls}
                      </td>
                      <td className="font-mono-tabular px-3.5 py-2.5 text-[#58413F]">
                        {formatPercent(row.precision, 1)}
                      </td>
                      <td className="font-mono-tabular px-3.5 py-2.5 text-[#58413F]">
                        {formatPercent(row.recall, 1)}
                      </td>
                      <td className="font-mono-tabular px-3.5 py-2.5 text-[#58413F]">
                        {formatPercent(row.f1, 1)}
                      </td>
                      <td className="font-mono-tabular px-3.5 py-2.5 text-right font-bold text-[#251918]">
                        {row.support}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card bgColor="elevated" className="space-y-4">
            <div>
              <h3 className="font-display text-xl font-normal text-[#251918]">
                Confusion Matrix
              </h3>
              <p className="mt-0.5 text-xs text-[#58413F]">
                Baris = kelas aktual, kolom = kelas terprediksi.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-separate border-spacing-1.5 text-center text-xs">
                <thead>
                  <tr>
                    <th className="p-2 text-left font-bold text-[#58413F]">
                      Aktual \ Prediksi
                    </th>
                    {cmLabels.map((lbl) => (
                      <th
                        key={lbl}
                        className="p-2 font-bold uppercase text-[#251918]"
                      >
                        {lbl}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {metrics.confusion_matrix.map((row, rIdx) => (
                    <tr key={cmLabels[rIdx] ?? rIdx}>
                      <td className="p-2 text-left font-bold uppercase text-[#251918]">
                        {cmLabels[rIdx] ?? rIdx}
                      </td>
                      {row.map((val, cIdx) => {
                        const isDiag = rIdx === cIdx;
                        return (
                          <td
                            key={cIdx}
                            className={
                              isDiag
                                ? 'font-mono-tabular rounded-[12px] border border-[#7E1117]/30 bg-[#FFF0EF] p-3 text-sm font-bold text-[#7E1117]'
                                : 'font-mono-tabular rounded-[12px] border border-[#DFBFBC] bg-[#FFF8F7] p-3 text-sm text-[#58413F]'
                            }
                          >
                            {val}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
