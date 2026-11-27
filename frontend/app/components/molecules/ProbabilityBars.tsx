'use client';

import React from 'react';
import { PredictedClass } from '@/model/Prediction';
import { cn } from '@/utils/classNames';
import { formatPercent, PREDICTED_CLASS_META } from '@/utils/formatters';

const ORDERED_CLASSES: PredictedClass[] = ['small', 'medium', 'large'];

export function ProbabilityBars({
  probabilities,
}: {
  probabilities: Record<string, number>;
}) {
  return (
    <div className="space-y-3">
      {ORDERED_CLASSES.map((cls) => {
        const value = Number(probabilities?.[cls] ?? 0);
        const meta = PREDICTED_CLASS_META[cls];
        const widthPct = Math.max(0, Math.min(100, value * 100));

        return (
          <div key={cls} className="space-y-1.5">
            <div className="flex items-center justify-between text-[13px]">
              <span className="font-bold text-[#251918]">{meta.label}</span>
              <span className="font-mono-tabular font-medium text-[#58413F]">
                {formatPercent(value, 1)}
              </span>
            </div>
            <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#FAE3E1]">
              <div
                className={cn(
                  'h-full rounded-full transition-all duration-300 ease-[cubic-bezier(0.2,0,0,1)]',
                  meta.barClass
                )}
                style={{ width: `${widthPct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
