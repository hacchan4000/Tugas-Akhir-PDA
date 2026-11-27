'use client';

import * as React from 'react';
import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import FormHelperText from '@mui/material/FormHelperText';
import MenuItem from '@mui/material/MenuItem';
import Select, { SelectChangeEvent } from '@mui/material/Select';
import { formatCategoryLabel } from '@/utils/formatters';

export interface CategoryOption {
  value: string;
  label: string;
}

interface CategoryProps {
  id?: string;
  label: string;
  value: string;
  onChange: (event: SelectChangeEvent) => void;
  options?: Array<CategoryOption | string>;
  error?: string;
  disabled?: boolean;
  size?: 'small' | 'medium';
}

export default function CategoryInput({
  id,
  label,
  value,
  onChange,
  options = [],
  error,
  disabled = false,
  size = 'small',
}: CategoryProps) {
  const reactId = React.useId();
  const labelId = `${id ?? reactId}-label`;
  const selectId = id ?? reactId;

  const normalizedOptions: CategoryOption[] = React.useMemo(
    () =>
      options.map((opt) =>
        typeof opt === 'string'
          ? { value: opt, label: formatCategoryLabel(opt) }
          : opt
      ),
    [options]
  );

  return (
    <Box sx={{ minWidth: 120, width: '100%' }}>
      <label
        id={labelId}
        htmlFor={selectId}
        className="mb-1.5 block text-[13px] font-bold tracking-[0.15px] text-[#251918]"
      >
        {label}
      </label>
      <FormControl fullWidth error={!!error} size={size} disabled={disabled}>
        <Select
          labelId={labelId}
          id={selectId}
          value={value}
          onChange={onChange}
          displayEmpty
          sx={{
            borderRadius: '12px',
            bgcolor: '#FFFFFF',
            color: '#251918',
            fontSize: '14px',
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: '#DFBFBC',
              borderWidth: '1px',
            },
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: '#8B716E',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: '#7E1117',
              borderWidth: '2px',
            },
          }}
        >
          {normalizedOptions.length === 0 ? (
            <MenuItem value="" disabled>
              Memuat opsi...
            </MenuItem>
          ) : (
            normalizedOptions.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))
          )}
        </Select>
        {error && (
          <FormHelperText sx={{ mx: 0, color: '#BA1A1A' }}>{error}</FormHelperText>
        )}
      </FormControl>
    </Box>
  );
}
