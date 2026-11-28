import { PredictedClass } from '@/model/Prediction';

const CATEGORY_LABELS: Record<string, string> = {
  complex: 'Kompleks',
  creep: 'Rayapan',
  debris_flow: 'Aliran Puing',
  earth_flow: 'Aliran Tanah',
  lahar: 'Lahar',
  landslide: 'Longsor',
  mudslide: 'Longsor Lumpur',
  riverbank_collapse: 'Keruntuhan Tebing Sungai',
  rock_fall: 'Jatuhan Batu',
  snow_avalanche: 'Longsoran Salju',
  topple: 'Terjungkir',
  translational_slide: 'Longsor Translasi',
  construction: 'Konstruksi',
  continuous_rain: 'Hujan Berkelanjutan',
  dam_embankment_collapse: 'Runtuhnya Bendungan/Tanggul',
  downpour: 'Hujan Deras',
  earthquake: 'Gempa Bumi',
  flooding: 'Banjir',
  freeze_thaw: 'Pembekuan-Pencairan',
  leaking_pipe: 'Pipa Bocor',
  mining: 'Pertambangan',
  monsoon: 'Muson',
  no_apparent_trigger: 'Tidak Ada Pemicu yang Tampak',
  rain: 'Hujan',
  snowfall_snowmelt: 'Curah Salju/Pencairan Salju',
  tropical_cyclone: 'Siklon Tropis',
  vibration: 'Getaran',
  volcano: 'Gunung Api',
  above_coast: 'Di Atas Pantai',
  above_river: 'Di Atas Sungai',
  above_road: 'Di Atas Jalan',
  below_road: 'Di Bawah Jalan',
  bluff: 'Tebing',
  burned_area: 'Area Terbakar',
  deforested_slope: 'Lereng Deforestasi',
  engineered_slope: 'Lereng Rekayasa',
  mine: 'Tambang',
  natural_slope: 'Lereng Alami',
  retaining_wall: 'Dinding Penahan',
  urban: 'Perkotaan',
  '100km': '100 km',
  '10km': '10 km',
  '1km': '1 km',
  '250km': '250 km',
  '25km': '25 km',
  '50km': '50 km',
  '5km': '5 km',
  exact: 'Lokasi Tepat',
  other: 'Lainnya',
  unknown: 'Tidak Diketahui',
};

export function formatCategoryLabel(value: string): string {
  if (!value) return '-';
  if (CATEGORY_LABELS[value]) return CATEGORY_LABELS[value];
  return value
    .split('_')
    .map((part) => (part ? part.charAt(0).toUpperCase() + part.slice(1) : ''))
    .join(' ');
}

export function formatDateTimeID(iso: string | null | undefined): string {
  if (!iso) return '-';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function formatDateID(iso: string | null | undefined): string {
  if (!iso) return '-';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat('id-ID', {
    dateStyle: 'medium',
  }).format(date);
}

export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '-';
  return `${(value * 100).toFixed(digits)}%`;
}

export const PREDICTED_CLASS_META: Record<
  PredictedClass,
  {
    label: string;
    badgeClass: string;
    barClass: string;
    sarBadgeClass: string;
  }
> = {
  small: {
    label: 'Kecil (Small)',
    badgeClass:
      'bg-[#ABECDE]/60 text-[#26695E] border border-[#26695E]/30',
    barClass: 'bg-[#26695E]',
    sarBadgeClass:
      'bg-[#ABECDE]/60 text-[#26695E] border border-[#26695E]/30',
  },
  medium: {
    label: 'Sedang (Medium)',
    badgeClass:
      'bg-[#FFF0EF] text-[#00464E] border border-[#005F6A]/30',
    barClass: 'bg-[#005F6A]',
    sarBadgeClass:
      'bg-[#8FD7E3]/35 text-[#00464E] border border-[#00464E]/30',
  },
  large: {
    label: 'Besar (Large)',
    badgeClass:
      'bg-[#FFDAD6] text-[#7E1117] border border-[#7E1117]/30',
    barClass: 'bg-[#7E1117]',
    sarBadgeClass:
      'bg-[#7E1117] text-white border border-[#7E1117]',
  },
};
