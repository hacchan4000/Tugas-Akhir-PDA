import { PredictedClass } from '@/model/Prediction';

export function formatCategoryLabel(value: string): string {
  if (!value) return '-';
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
