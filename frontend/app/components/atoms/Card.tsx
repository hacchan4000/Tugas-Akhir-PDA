import { cn } from '@/utils/classNames';
import React from 'react';

type CardVariant =
  | 'default'
  | 'thisWeek'
  | 'aiPrediction'
  | 'addPurchase'
  | 'latestPurchase'
  | 'graphsAi';

interface CardProps {
  children: React.ReactNode;
  border?: boolean;
  shadow?: boolean;
  blur?: boolean;
  bgColor?:
    | 'elevated'
    | 'tinted'
    | 'liquid-glass'
    | 'dark-grey'
    | 'semiTransparent'
    | 'secondary'
    | 'primary';
  className?: string;
  onClick?: () => void;
  variant?: CardVariant;
}

const variantClass: Record<CardVariant, string | undefined> = {
  default: undefined,
  thisWeek: 'flex flex-col justify-between w-[100%] max-w-[300px] h-[300px]',
  aiPrediction: 'flex flex-col justify-between w-[100%] max-w-[300px] h-[319px]',
  addPurchase:
    'flex flex-col items-end justify-between w-[100%] max-w-[300px] h-[300px] transition-[box-shadow,border-color] duration-150 ease-[cubic-bezier(0.2,0,0,1)] hover:border-[#7E1117]',
  latestPurchase: 'w-[100%] max-w-[660px]',
  graphsAi: 'flex flex-col justify-between w-[100%] max-w-[297px] md:shrink-0',
};

const Card = ({
  children,
  bgColor = 'elevated',
  border = false,
  shadow = true,
  className,
  onClick,
  variant = 'default',
}: CardProps) => {
  return (
    <div
      onClick={onClick}
      className={cn(
        'rounded-[24px] p-8 transition-all duration-150 ease-[cubic-bezier(0.2,0,0,1)]',
        (bgColor === 'elevated' || bgColor === 'liquid-glass') &&
          'bg-white border border-[#DFBFBC] text-[#251918]',
        bgColor === 'tinted' &&
          'bg-[#FFF0EF] border border-[#DFBFBC] text-[#251918]',
        bgColor === 'secondary' &&
          'bg-[#26695E] text-white border border-[#26695E]',
        bgColor === 'dark-grey' &&
          'bg-[#3B2D2C] text-[#FFEDEB] border border-[#58413F]',
        bgColor === 'semiTransparent' &&
          'bg-white/80 backdrop-blur-md border border-[#DFBFBC] text-[#251918]',
        bgColor === 'primary' &&
          'bg-[#7E1117] text-white border border-[#7E1117]',
        border && 'border-2 border-[#7E1117]',
        shadow &&
          'shadow-[0_16px_40px_-12px_rgba(37,25,24,0.08),0_4px_12px_-2px_rgba(37,25,24,0.04)]',
        variantClass[variant],
        className
      )}
    >
      {children}
    </div>
  );
};

export default Card;
