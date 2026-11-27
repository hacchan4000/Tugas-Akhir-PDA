'use client';

import React, { useState } from 'react';
import dayjs, { Dayjs } from 'dayjs';
import { MdMyLocation, MdPlayArrow, MdRefresh } from 'react-icons/md';
import Button from '@/app/components/atoms/Button';
import Card from '@/app/components/atoms/Card';
import CategoryInput from '@/app/components/atoms/CategoryInput';
import DateInput from '@/app/components/atoms/DateInput';
import TextInput from '@/app/components/atoms/TextInput';
import { showToast } from '@/app/components/atoms/toast';
import { useHist } from '@/hooks/useHist';
import { PredictionCreate } from '@/model/Prediction';

interface FormErrors {
  event_date?: string;
  latitude?: string;
  longitude?: string;
  landslide_category?: string;
  landslide_trigger?: string;
  landslide_setting?: string;
  location_accuracy?: string;
}

const SAMPLE_LOCATIONS = [
  { label: 'Bogor, Jawa Barat', lat: '-6.597147', lon: '106.806039' },
  { label: 'Banjarnegara, Jawa Tengah', lat: '-7.397600', lon: '109.696700' },
  { label: 'Manado, Sulawesi Utara', lat: '1.474830', lon: '124.842079' },
];

export function PredictionForm() {
  const { metaOptions, loadingMeta, submittingPrediction, createPrediction } =
    useHist();

  const [eventDate, setEventDate] = useState<Dayjs | null>(dayjs());
  const [latitude, setLatitude] = useState<string>('-6.597147');
  const [longitude, setLongitude] = useState<string>('106.806039');
  const [landslideCategory, setLandslideCategory] = useState<string>('landslide');
  const [landslideTrigger, setLandslideTrigger] = useState<string>('downpour');
  const [landslideSetting, setLandslideSetting] = useState<string>('natural_slope');
  const [locationAccuracy, setLocationAccuracy] = useState<string>('exact');
  const [errors, setErrors] = useState<FormErrors>({});

  const resolveOption = (current: string, allowed?: string[]) =>
    allowed?.length && !allowed.includes(current) ? allowed[0] : current;

  const effectiveCategory = resolveOption(
    landslideCategory,
    metaOptions?.valid_categories.landslide_category
  );
  const effectiveTrigger = resolveOption(
    landslideTrigger,
    metaOptions?.valid_categories.landslide_trigger
  );
  const effectiveSetting = resolveOption(
    landslideSetting,
    metaOptions?.valid_categories.landslide_setting
  );
  const effectiveAccuracy = resolveOption(
    locationAccuracy,
    metaOptions?.valid_categories.location_accuracy
  );

  const maxDate = metaOptions?.max_event_date
    ? dayjs(metaOptions.max_event_date)
    : dayjs();

  const validate = (): PredictionCreate | null => {
    const nextErrors: FormErrors = {};

    if (!eventDate || !eventDate.isValid()) {
      nextErrors.event_date = 'Tanggal kejadian wajib diisi (YYYY-MM-DD)';
    } else if (eventDate.isAfter(maxDate, 'day')) {
      nextErrors.event_date = `Tanggal tidak boleh melebihi ${maxDate.format('YYYY-MM-DD')}`;
    }

    const latNum = Number(latitude);
    const lonNum = Number(longitude);
    const [minLat, maxLat] = metaOptions?.coordinate_bounds.latitude ?? [-90, 90];
    const [minLon, maxLon] = metaOptions?.coordinate_bounds.longitude ?? [-180, 180];

    if (latitude.trim() === '' || Number.isNaN(latNum)) {
      nextErrors.latitude = 'Latitude harus berupa angka valid';
    } else if (latNum < minLat || latNum > maxLat) {
      nextErrors.latitude = `Latitude harus di antara ${minLat} dan ${maxLat}`;
    }

    if (longitude.trim() === '' || Number.isNaN(lonNum)) {
      nextErrors.longitude = 'Longitude harus berupa angka valid';
    } else if (lonNum < minLon || lonNum > maxLon) {
      nextErrors.longitude = `Longitude harus di antara ${minLon} dan ${maxLon}`;
    }

    if (!effectiveCategory) nextErrors.landslide_category = 'Kategori longsor wajib dipilih';
    if (!effectiveTrigger) nextErrors.landslide_trigger = 'Pemicu longsor wajib dipilih';
    if (!effectiveSetting) nextErrors.landslide_setting = 'Kondisi lokasi wajib dipilih';
    if (!effectiveAccuracy) nextErrors.location_accuracy = 'Akurasi lokasi wajib dipilih';

    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0 || !eventDate) {
      return null;
    }

    return {
      event_date: eventDate.format('YYYY-MM-DD'),
      latitude: latNum,
      longitude: lonNum,
      landslide_category: effectiveCategory,
      landslide_trigger: effectiveTrigger,
      landslide_setting: effectiveSetting,
      location_accuracy: effectiveAccuracy,
    };
  };

  const handleUseMyLocation = () => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      showToast('Browser tidak mendukung geolokasi', 'warning');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude.toFixed(6));
        setLongitude(pos.coords.longitude.toFixed(6));
        showToast('Koordinat GPS berhasil diambil', 'info');
      },
      () => {
        showToast('Gagal mengambil lokasi GPS (izin ditolak atau tidak tersedia)', 'warning');
      }
    );
  };

  const handleReset = () => {
    setEventDate(dayjs());
    setLatitude('-6.597147');
    setLongitude('106.806039');
    setLandslideCategory(metaOptions?.valid_categories.landslide_category?.[0] ?? 'landslide');
    setLandslideTrigger(metaOptions?.valid_categories.landslide_trigger?.[0] ?? 'downpour');
    setLandslideSetting(metaOptions?.valid_categories.landslide_setting?.[0] ?? 'natural_slope');
    setLocationAccuracy(metaOptions?.valid_categories.location_accuracy?.[0] ?? 'exact');
    setErrors({});
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = validate();
    if (!payload) return;
    await createPrediction(payload);
  };

  return (
    <Card bgColor="elevated" className="w-full">
      <div className="mb-6 flex flex-col gap-3 border-b border-[#DFBFBC]/60 pb-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-[26px] font-normal leading-8 text-[#251918]">
            Parameter Kejadian Tanah Longsor
          </h2>
          <p className="mt-1 text-sm text-[#58413F]">
            Masukkan koordinat geospasial dan karakteristik kejadian untuk mengklasifikasikan skala bahaya dan prioritas tim SAR.
          </p>
        </div>
        <button
          type="button"
          onClick={handleUseMyLocation}
          className="inline-flex shrink-0 items-center gap-1.5 self-start rounded-[12px] border border-[#26695E]/35 bg-[#ABECDE]/40 px-3.5 py-2 text-xs font-bold text-[#26695E] transition duration-150 ease-[cubic-bezier(0.2,0,0,1)] hover:bg-[#ABECDE]/70 cursor-pointer"
        >
          <MdMyLocation className="text-sm" />
          Koordinat GPS
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <DateInput
            label="Tanggal Kejadian"
            value={eventDate}
            onChange={(val) => setEventDate(val)}
            maxDate={maxDate}
            error={errors.event_date}
            disabled={submittingPrediction}
          />

          <TextInput
            label="Latitude"
            variant="outlined"
            type="number"
            step="any"
            placeholder="-6.597147"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            error={errors.latitude}
            disabled={submittingPrediction}
          />

          <TextInput
            label="Longitude"
            variant="outlined"
            type="number"
            step="any"
            placeholder="106.806039"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            error={errors.longitude}
            disabled={submittingPrediction}
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 rounded-[12px] bg-[#FFF0EF] px-4 py-2.5 text-xs">
          <span className="font-bold text-[#58413F]">Referensi koordinat:</span>
          {SAMPLE_LOCATIONS.map((sample) => (
            <button
              key={sample.label}
              type="button"
              onClick={() => {
                setLatitude(sample.lat);
                setLongitude(sample.lon);
              }}
              className="rounded-[8px] border border-[#DFBFBC] bg-white px-2.5 py-1 font-medium text-[#251918] transition duration-150 hover:border-[#7E1117] hover:text-[#7E1117] cursor-pointer"
            >
              {sample.label}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <CategoryInput
            id="landslide_category"
            label="Kategori Longsor"
            value={effectiveCategory}
            onChange={(e) => setLandslideCategory(e.target.value)}
            options={metaOptions?.valid_categories.landslide_category ?? []}
            error={errors.landslide_category}
            disabled={loadingMeta || submittingPrediction}
          />

          <CategoryInput
            id="landslide_trigger"
            label="Pemicu Longsor"
            value={effectiveTrigger}
            onChange={(e) => setLandslideTrigger(e.target.value)}
            options={metaOptions?.valid_categories.landslide_trigger ?? []}
            error={errors.landslide_trigger}
            disabled={loadingMeta || submittingPrediction}
          />

          <CategoryInput
            id="landslide_setting"
            label="Kondisi Lingkungan"
            value={effectiveSetting}
            onChange={(e) => setLandslideSetting(e.target.value)}
            options={metaOptions?.valid_categories.landslide_setting ?? []}
            error={errors.landslide_setting}
            disabled={loadingMeta || submittingPrediction}
          />

          <CategoryInput
            id="location_accuracy"
            label="Akurasi Lokasi"
            value={effectiveAccuracy}
            onChange={(e) => setLocationAccuracy(e.target.value)}
            options={metaOptions?.valid_categories.location_accuracy ?? []}
            error={errors.location_accuracy}
            disabled={loadingMeta || submittingPrediction}
          />
        </div>

        <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
          <Button
            label="Reset"
            variant="outlined"
            color="secondary"
            prefix={<MdRefresh />}
            onClick={handleReset}
            disabled={submittingPrediction}
          />
          <Button
            type="submit"
            label={submittingPrediction ? 'Memproses...' : 'Klasifikasikan Kejadian'}
            variant="contained"
            color="primary"
            prefix={<MdPlayArrow />}
            disabled={submittingPrediction || loadingMeta}
            className="px-6"
          />
        </div>
      </form>
    </Card>
  );
}
