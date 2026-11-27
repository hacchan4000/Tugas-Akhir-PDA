'use client';

import { cn } from '@/utils/classNames';
import { motion } from 'framer-motion';

interface ButtonProps {
  label?: React.ReactNode;
  children?: React.ReactNode;
  onClick?: (event: React.MouseEvent<HTMLElement>) => void;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  color?: 'primary' | 'secondary' | 'blue' | 'black';
  variant?: 'text' | 'outlined' | 'contained' | 'primary' | 'ghost' | 'white';
  disabled?: boolean;
  type?: 'button' | 'submit';
  shape?: 'default' | 'pill';
  className?: string;
  fullWidth?: boolean;
}

const Button = ({
  children,
  label,
  onClick,
  prefix,
  suffix,
  color = 'primary',
  variant = 'contained',
  disabled = false,
  type = 'button',
  fullWidth = false,
  shape = 'default',
  className,
}: ButtonProps) => {
  const styles: string[] = [];

  if (variant === 'contained' || variant === 'primary') {
    if (color === 'primary') {
      styles.push(
        'bg-[#7E1117] text-white enabled:hover:bg-[#9F2B2B] shadow-sm'
      );
    } else if (color === 'secondary') {
      styles.push(
        'bg-[#26695E] text-white enabled:hover:bg-[#1D5249] shadow-sm'
      );
    } else if (color === 'blue') {
      styles.push(
        'bg-[#00464E] text-white enabled:hover:bg-[#005F6A] shadow-sm'
      );
    } else if (color === 'black') {
      styles.push(
        'bg-[#251918] text-white enabled:hover:bg-[#3B2D2C] shadow-sm'
      );
    }
  }

  if (variant === 'outlined') {
    styles.push('border bg-white');
    if (color === 'primary') {
      styles.push(
        'border-[#7E1117] text-[#7E1117] enabled:hover:bg-[#FFF0EF]'
      );
    } else if (color === 'secondary') {
      styles.push(
        'border-[#DFBFBC] text-[#58413F] enabled:hover:border-[#8B716E] enabled:hover:bg-[#FFF0EF] enabled:hover:text-[#251918]'
      );
    } else if (color === 'blue') {
      styles.push(
        'border-[#26695E] text-[#26695E] enabled:hover:bg-[#ABECDE]/30'
      );
    }
  }

  if (variant === 'text' || variant === 'ghost') {
    styles.push('bg-transparent');
    if (color === 'primary') {
      styles.push('text-[#7E1117] enabled:hover:bg-[#FFF0EF]');
    } else {
      styles.push('text-[#58413F] enabled:hover:bg-[#FAE3E1]/60');
    }
  }

  if (variant === 'white') {
    styles.push(
      'border border-[#DFBFBC] bg-white text-[#251918] enabled:hover:bg-[#FFF0EF]'
    );
  }

  if (shape === 'pill') {
    styles.push('rounded-full px-6 py-3');
  }

  if (fullWidth) {
    styles.push('w-full');
  }

  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.01 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      transition={{ duration: 0.15, ease: [0.2, 0, 0, 1] }}
      className={cn(
        'inline-flex items-center justify-center rounded-[12px] px-4 py-2.5 text-[15px] font-bold tracking-[0.2px] transition-colors duration-150 ease-[cubic-bezier(0.2,0,0,1)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#7E1117]',
        disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer',
        styles.join(' '),
        className
      )}
      onClick={onClick}
      type={type}
      disabled={disabled}
    >
      {prefix && <span className="mr-2 inline-flex items-center">{prefix}</span>}
      {label !== undefined && label !== '' && <span>{label}</span>}
      {children}
      {suffix && <span className="ml-2 inline-flex items-center">{suffix}</span>}
    </motion.button>
  );
};

export default Button;
