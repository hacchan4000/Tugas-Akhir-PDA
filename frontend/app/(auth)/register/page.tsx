'use client';

import React, { useEffect } from 'react';
import { joiResolver } from '@hookform/resolvers/joi';
import { Controller, useForm } from 'react-hook-form';
import { useRouter } from 'next/navigation';
import Button from '@/app/components/atoms/Button';
import TextInput from '@/app/components/atoms/TextInput';
import { useAuth } from '@/hooks/useAuth';
import { registerSchema } from './schema';

type RegisterForm = {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
};

export default function RegisterPage() {
  const router = useRouter();
  const { register, isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace('/');
    }
  }, [loading, isAuthenticated, router]);

  const {
    handleSubmit,
    control,
    formState: { isSubmitting, isValid },
  } = useForm<RegisterForm>({
    resolver: joiResolver(registerSchema),
    mode: 'onChange',
    defaultValues: {
      name: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  });

  const onSubmit = async (data: RegisterForm) => {
    await register(data.name.trim(), data.email.trim(), data.password);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div>
        <h2 className="font-display text-[28px] leading-[36px] text-[#251918]">
          Daftar Akun Operator
        </h2>
        <p className="mt-1 text-sm text-[#58413F]">
          Buat akun baru untuk mengakses klasifikasi longsor dan menyimpan riwayat SAR.
        </p>
      </div>

      <Controller
        name="name"
        control={control}
        render={({ field, fieldState }) => (
          <TextInput
            label="Nama Operator"
            variant="outlined"
            type="text"
            placeholder="Contoh: Budi Santoso"
            {...field}
            error={fieldState.error?.message}
            disabled={isSubmitting}
          />
        )}
      />

      <Controller
        name="email"
        control={control}
        render={({ field, fieldState }) => (
          <TextInput
            label="E-mail"
            variant="outlined"
            type="email"
            placeholder="operator@basarnas.go.id"
            {...field}
            error={fieldState.error?.message}
            disabled={isSubmitting}
          />
        )}
      />

      <Controller
        name="password"
        control={control}
        render={({ field, fieldState }) => (
          <TextInput
            label="Password"
            variant="outlined"
            type="password"
            placeholder="Minimal 8 karakter"
            {...field}
            error={fieldState.error?.message}
            disabled={isSubmitting}
          />
        )}
      />

      <Controller
        name="confirmPassword"
        control={control}
        render={({ field, fieldState }) => (
          <TextInput
            label="Konfirmasi Password"
            variant="outlined"
            type="password"
            placeholder="Ulangi password"
            {...field}
            error={fieldState.error?.message}
            disabled={isSubmitting}
          />
        )}
      />

      <Button
        type="submit"
        label={isSubmitting ? 'Mendaftarkan...' : 'Daftar Akun'}
        variant="contained"
        color="primary"
        fullWidth
        className="h-12"
        disabled={!isValid || isSubmitting}
      />

      <div className="border-t border-[#DFBFBC] pt-4 text-center text-[13px] text-[#58413F]">
        Sudah memiliki akun operator?{' '}
        <button
          type="button"
          onClick={() => router.push('/login')}
          className="font-bold text-[#7E1117] underline decoration-[#7E1117]/40 underline-offset-4 transition duration-150 hover:text-[#9F2B2B] cursor-pointer"
        >
          Log in di sini
        </button>
      </div>
    </form>
  );
}
