'use client';

import React from 'react';
import { PredictedClass } from '@/model/Prediction';
import { cn } from '@/utils/classNames';
import { PREDICTED_CLASS_META } from '@/utils/formatters';

export function PredictedClassBadge({
  predictedClass,
  className,
}: {
  predictedClass: PredictedClass;
  className?: string;
}) {
  const meta = PREDICTED_CLASS_META[predictedClass] ?? PREDICTED_CLASS_META.medium;
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-bold tracking-[0.2px]',
        meta.badgeClass,
        className
      )}
    >
      {meta.label}
    </span>
  );
}

export function SarPriorityBadge({
  predictedClass,
  level,
  className,
}: {
  predictedClass: PredictedClass;
  level: string;
  className?: string;
}) {
  const meta = PREDICTED_CLASS_META[predictedClass] ?? PREDICTED_CLASS_META.medium;
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-3 py-1 text-xs font-bold uppercase tracking-[0.25px]',
        meta.sarBadgeClass,
        className
      )}
    >
      Prioritas SAR: {level || '-'}
    </span>
  );
}
