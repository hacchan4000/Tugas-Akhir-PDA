'use client';

import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { Dayjs } from 'dayjs';

interface DateProps {
  label: string;
  value: Dayjs | null;
  onChange: (value: Dayjs | null) => void;
  error?: string;
  maxDate?: Dayjs;
  minDate?: Dayjs;
  disabled?: boolean;
}

export default function DateInput({
  label,
  value,
  onChange,
  error,
  maxDate,
  minDate,
  disabled = false,
}: DateProps) {
  return (
    <div className="flex w-full flex-col gap-1.5">
      <label className="text-[13px] font-bold tracking-[0.15px] text-[#251918]">
        {label}
      </label>
      <DatePicker
        value={value}
        onChange={onChange}
        maxDate={maxDate}
        minDate={minDate}
        disabled={disabled}
        format="YYYY-MM-DD"
        slotProps={{
          textField: {
            fullWidth: true,
            size: 'small',
            error: !!error,
            helperText: error,
            sx: {
              '& .MuiFormHelperText-root': {
                mx: 0,
                color: '#BA1A1A',
              },
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
            },
          },
        }}
      />
    </div>
  );
}
