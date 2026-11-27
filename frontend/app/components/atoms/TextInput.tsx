'use client';

import { IconButton, InputAdornment, TextField } from '@mui/material';
import React from 'react';
import { MdVisibility, MdVisibilityOff } from 'react-icons/md';

type Variant = 'standard' | 'outlined';

interface TextInputProps {
  label: string;
  value: string | number | undefined;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  className?: string;
  error?: string;
  type?: string;
  variant?: Variant;
  disabled?: boolean;
  placeholder?: string;
  step?: string;
}

export default function TextInput({
  label,
  value,
  onChange,
  className = '',
  error,
  type = 'text',
  variant = 'outlined',
  disabled = false,
  placeholder,
  step,
}: TextInputProps) {
  const [showPassword, setShowPassword] = React.useState(false);

  const isPasswordType = type === 'password';

  const inputType = React.useMemo(() => {
    if (!isPasswordType) return type;
    return showPassword ? 'text' : 'password';
  }, [type, isPasswordType, showPassword]);

  const hasValue = value !== '' && value !== null && value !== undefined;

  return (
    <div className={`flex w-full flex-col gap-1.5 ${className}`}>
      {variant === 'outlined' && (
        <label className="text-[13px] font-bold tracking-[0.15px] text-[#251918]">
          {label}
        </label>
      )}

      <TextField
        label={variant === 'standard' ? label : ''}
        value={value ?? ''}
        onChange={onChange}
        fullWidth
        type={inputType}
        placeholder={placeholder}
        error={!!error}
        helperText={error}
        variant={variant}
        disabled={disabled}
        slotProps={{
          htmlInput: step ? { step } : undefined,
          input: {
            endAdornment: isPasswordType && (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowPassword((prev) => !prev)}
                  edge="end"
                  aria-label="Tampilkan atau sembunyikan password"
                  sx={{ color: '#58413F' }}
                >
                  {showPassword ? <MdVisibility /> : <MdVisibilityOff />}
                </IconButton>
              </InputAdornment>
            ),
          },
          inputLabel:
            variant === 'standard'
              ? {
                  sx: {
                    fontSize: '15px',
                    fontWeight: 700,
                    color: hasValue ? '#58413F' : '#8B716E',
                    '&.Mui-focused': {
                      color: '#7E1117',
                    },
                    '&.Mui-error': {
                      color: '#BA1A1A',
                    },
                  },
                }
              : { shrink: true },
        }}
        sx={{
          '& .MuiFormHelperText-root': {
            marginLeft: 0,
            fontSize: '12px',
            color: '#BA1A1A',
          },
          ...(variant === 'standard' && {
            '& .MuiInput-input': {
              color: '#251918',
              fontSize: '15px',
            },
            '& .MuiInput-root:after': {
              borderBottomColor: '#7E1117',
              borderBottomWidth: '2px',
            },
            '& .MuiInput-root:hover:not(.Mui-disabled):before': {
              borderBottomColor: '#7E1117',
            },
            '& .MuiInput-root:before': {
              borderBottomColor: hasValue ? '#7E1117' : '#DFBFBC',
              borderBottomWidth: hasValue ? '2px' : '1px',
            },
          }),
          ...(variant === 'outlined' && {
            '& .MuiOutlinedInput-root': {
              borderRadius: '12px',
              backgroundColor: '#FFFFFF',
              color: '#251918',
              transition: 'border-color 150ms cubic-bezier(0.2, 0, 0, 1)',
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
              '&.Mui-error fieldset': {
                borderColor: '#BA1A1A',
              },
            },
            '& .MuiOutlinedInput-input': {
              paddingTop: '10px',
              paddingBottom: '10px',
              paddingLeft: '14px',
              paddingRight: '14px',
              fontSize: '14px',
              '&::placeholder': {
                color: '#8B716E',
                opacity: 1,
              },
            },
          }),
        }}
      />
    </div>
  );
}
