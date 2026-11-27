'use client';

import React, { useMemo, useState } from 'react';
import Autocomplete from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import dayjs, { Dayjs } from 'dayjs';
import { MdLocationOn, MdMyLocation, MdPlayArrow, MdRefresh } from 'react-icons/md';
import Button from '@/app/components/atoms/Button';
import Card from '@/app/components/atoms/Card';
import CategoryInput from '@/app/components/atoms/CategoryInput';
import DateInput from '@/app/components/atoms/DateInput';
import TextInput from '@/app/components/atoms/TextInput';
import { showToast } from '@/app/components/atoms/toast';
import { useHist } from '@/hooks/useHist';
import { PredictionCreate } from '@/model/Prediction';
import {
  INDONESIA_PROVINCES,
  INDONESIA_REGIONS,
  RegionCoordinate,
} from '@/utils/indonesiaRegions';

interface FormErrors {
  event_date?: string;
  latitude?: string;
  longitude?: string;
  landslide_category?: string;
  landslide_trigger?: string;
  landslide_setting?: string;
  location_accuracy?: string;
}

type LocationSource = 'region' | 'gps' | 'manual';

const DEFAULT_REGION =
  INDONESIA_REGIONS.find((region) => region.id === 'jabar-kota-bogor') ??
  INDONESIA_REGIONS[0];

const PROVINCE_OPTIONS = [
  { value: 'ALL', label: 'Semua Provinsi' },
  ...INDONESIA_PROVINCES.map((province) => ({ value: province, label: province })),
];

export function PredictionForm() {
  const { metaOptions, loadingMeta, submittingPrediction, createPrediction } =
    useHist();

  const [eventDate, setEventDate] = useState<Dayjs | null>(dayjs());
  const [selectedProvince, setSelectedProvince] = useState<string>('ALL');
  const [selectedRegion, setSelectedRegion] = useState<RegionCoordinate | null>(
    DEFAULT_REGION
  );
  const [locationSource, setLocationSource] = useState<LocationSource>('region');
  const [latitude, setLatitude] = useState<string>(
    DEFAULT_REGION.latitude.toFixed(6)
  );
  const [longitude, setLongitude] = useState<string>(
    DEFAULT_REGION.longitude.toFixed(6)
  );
  const [landslideCategory, setLandslideCategory] = useState<string>('landslide');
  const [landslideTrigger, setLandslideTrigger] = useState<string>('downpour');
  const [landslideSetting, setLandslideSetting] = useState<string>('natural_slope');
  const [locationAccuracy, setLocationAccuracy] = useState<string>('exact');
  const [errors, setErrors] = useState<FormErrors>({});

  const filteredRegions = useMemo(
    () =>
      selectedProvince === 'ALL'
        ? INDONESIA_REGIONS
        : INDONESIA_REGIONS.filter((region) => region.province === selectedProvince),
    [selectedProvince]
  );

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

  const applyRegion = (region: RegionCoordinate | null) => {
    setSelectedRegion(region);
    if (region) {
      setLatitude(region.latitude.toFixed(6));
      setLongitude(region.longitude.toFixed(6));
      setLocationSource('region');
      setErrors((prev) => ({
        ...prev,
        latitude: undefined,
        longitude: undefined,
      }));
    } else {
      setLocationSource('manual');
    }
  };

  const handleProvinceChange = (nextProvince: string) => {
    setSelectedProvince(nextProvince);
    if (nextProvince === 'ALL') return;
    if (selectedRegion?.province !== nextProvince) {
      const firstInProvince =
        INDONESIA_REGIONS.find((region) => region.province === nextProvince) ?? null;
      applyRegion(firstInProvince);
    }
  };

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
        setSelectedRegion(null);
        setLocationSource('gps');
        setLatitude(pos.coords.latitude.toFixed(6));
        setLongitude(pos.coords.longitude.toFixed(6));
        setErrors((prev) => ({
          ...prev,
          latitude: undefined,
          longitude: undefined,
        }));
        showToast('Koordinat GPS terkini berhasil diambil', 'info');
      },
      () => {
        showToast('Gagal mengambil lokasi GPS (izin ditolak atau tidak tersedia)', 'warning');
      }
    );
  };

  const handleReset = () => {
    setEventDate(dayjs());
    setSelectedProvince('ALL');
    setSelectedRegion(DEFAULT_REGION);
    setLocationSource('region');
    setLatitude(DEFAULT_REGION.latitude.toFixed(6));
    setLongitude(DEFAULT_REGION.longitude.toFixed(6));
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
      <div className="mb-6 border-b border-[#DFBFBC]/60 pb-5">
        <h2 className="font-display text-[26px] font-normal leading-8 text-[#251918]">
          Parameter Kejadian Tanah Longsor
        </h2>
        <p className="mt-1 text-sm text-[#58413F]">
          Pilih daerah kejadian atau gunakan koordinat GPS / manual beserta karakteristik kejadian untuk mengklasifikasikan skala bahaya dan prioritas tim SAR.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <DateInput
          label="Tanggal Kejadian"
          value={eventDate}
          onChange={(val) => setEventDate(val)}
          maxDate={maxDate}
          error={errors.event_date}
          disabled={submittingPrediction}
        />

        <div className="space-y-4 rounded-[16px] border border-[#DFBFBC] bg-[#FFF8F7] p-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <MdLocationOn className="text-lg text-[#7E1117]" />
              <div>
                <h3 className="text-sm font-bold text-[#251918]">
                  Lokasi Kejadian
                </h3>
                <p className="text-xs text-[#58413F]">
                  Pilih daerah melalui dropdown untuk mengisi koordinat otomatis, atau gunakan GPS / input manual.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleUseMyLocation}
              disabled={submittingPrediction}
              className="inline-flex shrink-0 items-center gap-1.5 self-start rounded-[12px] border border-[#26695E]/35 bg-[#ABECDE]/40 px-3.5 py-2 text-xs font-bold text-[#26695E] transition duration-150 ease-[cubic-bezier(0.2,0,0,1)] hover:bg-[#ABECDE]/70 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer"
            >
              <MdMyLocation className="text-sm" />
              Lokasi Terkini (GPS)
            </button>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <CategoryInput
              id="region_province"
              label="Provinsi"
              value={selectedProvince}
              onChange={(e) => handleProvinceChange(e.target.value)}
              options={PROVINCE_OPTIONS}
              disabled={submittingPrediction}
            />

            <div className="flex w-full flex-col gap-1.5">
              <label
                htmlFor="region_city_autocomplete"
                className="text-[13px] font-bold tracking-[0.15px] text-[#251918]"
              >
                Daerah (Kota / Kabupaten)
              </label>
              <Autocomplete
                id="region_city_autocomplete"
                options={filteredRegions}
                value={selectedRegion}
                onChange={(_, value) => applyRegion(value)}
                getOptionLabel={(option) => option.name}
                isOptionEqualToValue={(option, value) => option.id === value.id}
                groupBy={
                  selectedProvince === 'ALL' ? (option) => option.province : undefined
                }
                disabled={submittingPrediction}
                noOptionsText="Daerah tidak ditemukan"
                renderInput={(params) => (
                  <TextField
                    {...params}
                    size="small"
                    placeholder="Cari atau pilih daerah..."
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: '12px',
                        backgroundColor: '#FFFFFF',
                        color: '#251918',
                        fontSize: '14px',
                        '& fieldset': {
                          borderColor: '#DFBFBC',
                          borderWidth: '1px',
                        },
                        '&:hover fieldset': {
                          borderColor: '#8B716E',
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: '#7E1117',
                          borderWidth: '2px',
                        },
                      },
                    }}
                  />
                )}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <TextInput
              label="Latitude"
              variant="outlined"
              type="number"
              step="any"
              placeholder="-6.597147"
              value={latitude}
              onChange={(e) => {
                setLatitude(e.target.value);
                setSelectedRegion(null);
                setLocationSource('manual');
              }}
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
              onChange={(e) => {
                setLongitude(e.target.value);
                setSelectedRegion(null);
                setLocationSource('manual');
              }}
              error={errors.longitude}
              disabled={submittingPrediction}
            />
          </div>

          <p className="text-xs text-[#58413F]">
            <span className="font-bold">Sumber koordinat:</span>{' '}
            {locationSource === 'region' && selectedRegion
              ? `${selectedRegion.name}, ${selectedRegion.province}`
              : locationSource === 'gps'
                ? 'Lokasi Terkini (GPS perangkat)'
                : 'Input Koordinat Manual'}
          </p>
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
