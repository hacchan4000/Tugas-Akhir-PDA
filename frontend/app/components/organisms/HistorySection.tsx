'use client';

import React, { useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import {
  MdChevronLeft,
  MdChevronRight,
  MdDownload,
  MdRefresh,
  MdSearch,
  MdVisibility,
} from 'react-icons/md';
import Button from '@/app/components/atoms/Button';
import Card from '@/app/components/atoms/Card';
import DateInput from '@/app/components/atoms/DateInput';
import TextInput from '@/app/components/atoms/TextInput';
import {
  PredictedClassBadge,
  SarPriorityBadge,
} from '@/app/components/molecules/ClassBadge';
import { useHist } from '@/hooks/useHist';
import { HistoryFilters } from '@/model/Prediction';
import {
  formatCategoryLabel,
  formatDateID,
  formatDateTimeID,
  formatPercent,
} from '@/utils/formatters';

export function HistorySection() {
  const {
    items,
    total,
    page,
    pages,
    filters,
    loadingHistory,
    exportingCsv,
    fetchHistory,
    openDetail,
    exportCsv,
    setFilters,
  } = useHist();

  const [dateFrom, setDateFrom] = useState<Dayjs | null>(
    filters.date_from ? dayjs(filters.date_from) : null
  );
  const [dateTo, setDateTo] = useState<Dayjs | null>(
    filters.date_to ? dayjs(filters.date_to) : null
  );
  const [region, setRegion] = useState<string>(filters.region ?? '');
  const [searchText, setSearchText] = useState<string>(filters.q ?? '');

  const applyFilters = async (nextPage = 1) => {
    const nextFilters: HistoryFilters = {
      ...filters,
      page: nextPage,
      date_from: dateFrom && dateFrom.isValid() ? dateFrom.format('YYYY-MM-DD') : '',
      date_to: dateTo && dateTo.isValid() ? dateTo.format('YYYY-MM-DD') : '',
      region: region.trim(),
      q: searchText.trim(),
    };
    setFilters(nextFilters);
    await fetchHistory(nextFilters);
  };

  const resetFilters = async () => {
    setDateFrom(null);
    setDateTo(null);
    setRegion('');
    setSearchText('');
    const clean: HistoryFilters = {
      page: 1,
      page_size: filters.page_size ?? 10,
      date_from: '',
      date_to: '',
      region: '',
      q: '',
    };
    setFilters(clean);
    await fetchHistory(clean);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void applyFilters(1);
  };

  return (
    <Card bgColor="elevated" className="w-full space-y-6">
      <div className="flex flex-col gap-3 border-b border-[#DFBFBC]/60 pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-[26px] font-normal leading-8 text-[#251918]">
            Riwayat Klasifikasi Operator
          </h2>
          <p className="mt-1 text-sm text-[#58413F]">
            Total <span className="font-mono-tabular font-bold">{total}</span> entri tersimpan. Filter berdasarkan rentang tanggal kejadian, wilayah, atau kata kunci.
          </p>
        </div>

        <Button
          label={exportingCsv ? 'Menyiapkan CSV...' : 'Ekspor CSV'}
          variant="contained"
          color="primary"
          prefix={<MdDownload />}
          disabled={exportingCsv || loadingHistory}
          onClick={() => void exportCsv()}
        />
      </div>

      <form
        onSubmit={handleSubmit}
        className="grid grid-cols-1 gap-4 rounded-[16px] border border-[#DFBFBC] bg-[#FFF8F7] p-4 sm:grid-cols-2 lg:grid-cols-5"
      >
        <DateInput
          label="Dari Tanggal"
          value={dateFrom}
          onChange={setDateFrom}
        />

        <DateInput
          label="Sampai Tanggal"
          value={dateTo}
          onChange={setDateTo}
        />

        <TextInput
          label="Wilayah"
          variant="outlined"
          placeholder="Contoh: Jawa Barat"
          value={region}
          onChange={(e) => setRegion(e.target.value)}
        />

        <TextInput
          label="Kata Kunci"
          variant="outlined"
          placeholder="Kategori / pemicu / wilayah"
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />

        <div className="flex items-end gap-2">
          <Button
            type="submit"
            label="Filter"
            variant="contained"
            color="secondary"
            prefix={<MdSearch />}
            disabled={loadingHistory}
            className="flex-1"
          />
          <Button
            label=""
            variant="outlined"
            color="secondary"
            prefix={<MdRefresh className="mr-0" />}
            onClick={() => void resetFilters()}
            disabled={loadingHistory}
            className="px-3"
          />
        </div>
      </form>

      <div className="overflow-x-auto rounded-[16px] border border-[#DFBFBC]">
        <table className="min-w-full divide-y divide-[#DFBFBC] text-left text-sm">
          <thead className="bg-[#FFF0EF] text-xs font-bold uppercase tracking-[0.25px] text-[#58413F]">
            <tr>
              <th className="px-4 py-3.5">ID</th>
              <th className="px-4 py-3.5">Tanggal</th>
              <th className="px-4 py-3.5">Wilayah / Koordinat</th>
              <th className="px-4 py-3.5">Kategori &amp; Pemicu</th>
              <th className="px-4 py-3.5">Skala</th>
              <th className="px-4 py-3.5">Prioritas SAR</th>
              <th className="px-4 py-3.5">Confidence</th>
              <th className="px-4 py-3.5 text-right">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#DFBFBC]/70 bg-white">
            {loadingHistory ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-[#58413F]">
                  Memuat riwayat klasifikasi...
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-[#58413F]">
                  Belum ada data klasifikasi yang sesuai dengan filter.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr
                  key={item.prediction_id}
                  className="transition duration-150 hover:bg-[#FFF8F7]"
                >
                  <td className="font-mono-tabular px-4 py-3.5 text-xs font-medium text-[#58413F]">
                    #{item.prediction_id}
                  </td>
                  <td className="px-4 py-3.5 text-xs text-[#251918]">
                    <div className="font-bold">{formatDateID(item.event_date)}</div>
                    <div className="text-[11px] text-[#8B716E]">
                      {formatDateTimeID(item.prediction_date)}
                    </div>
                  </td>
                  <td className="max-w-[230px] px-4 py-3.5 text-xs">
                    <div className="truncate font-bold text-[#251918]">
                      {item.nama_wilayah || 'Tidak diketahui'}
                    </div>
                    <div className="font-mono-tabular text-[11px] text-[#58413F]">
                      {item.latitude.toFixed(4)}, {item.longitude.toFixed(4)}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-xs text-[#251918]">
                    <div className="font-medium">
                      {formatCategoryLabel(item.landslide_category)}
                    </div>
                    <div className="text-[11px] text-[#58413F]">
                      {formatCategoryLabel(item.landslide_trigger)}
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <PredictedClassBadge predictedClass={item.predicted_class} />
                  </td>
                  <td className="px-4 py-3.5">
                    <SarPriorityBadge
                      predictedClass={item.predicted_class}
                      level={item.sar_priority_level}
                    />
                  </td>
                  <td className="font-mono-tabular px-4 py-3.5 text-xs font-bold text-[#251918]">
                    {formatPercent(item.confidence_score, 1)}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <button
                      type="button"
                      onClick={() => void openDetail(item.prediction_id)}
                      className="inline-flex items-center gap-1 rounded-[10px] border border-[#DFBFBC] bg-white px-3 py-1.5 text-xs font-bold text-[#7E1117] transition duration-150 hover:border-[#7E1117] hover:bg-[#FFF0EF] cursor-pointer"
                    >
                      <MdVisibility className="text-sm" />
                      Detail
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col items-center justify-between gap-3 text-xs text-[#58413F] sm:flex-row">
        <span>
          Halaman <span className="font-mono-tabular font-bold">{pages === 0 ? 0 : page}</span> dari{' '}
          <span className="font-mono-tabular font-bold">{pages}</span> ({total} total entri)
        </span>
        <div className="flex items-center gap-2">
          <Button
            label="Sebelumnya"
            variant="outlined"
            color="secondary"
            prefix={<MdChevronLeft />}
            disabled={loadingHistory || page <= 1}
            onClick={() => void applyFilters(page - 1)}
            className="px-3 py-1.5 text-xs"
          />
          <Button
            label="Berikutnya"
            variant="outlined"
            color="secondary"
            suffix={<MdChevronRight />}
            disabled={loadingHistory || pages === 0 || page >= pages}
            onClick={() => void applyFilters(page + 1)}
            className="px-3 py-1.5 text-xs"
          />
        </div>
      </div>
    </Card>
  );
}
