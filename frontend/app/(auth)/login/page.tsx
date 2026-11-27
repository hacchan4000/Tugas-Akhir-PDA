'use client';

import React, { useEffect } from 'react';
import Joi from 'joi';
import { joiResolver } from '@hookform/resolvers/joi';
import { Controller, useForm } from 'react-hook-form';
import { useRouter } from 'next/navigation';
import Button from '@/app/components/atoms/Button';
import TextInput from '@/app/components/atoms/TextInput';
import { useAuth } from '@/hooks/useAuth';

type LoginForm = {
  email: string;
  password: string;
};

const loginSchema = Joi.object({
  email: Joi.string()
    .email({ tlds: { allow: false } })
    .required()
    .messages({
      'string.empty': 'E-mail wajib diisi',
      'string.email': 'Format e-mail tidak valid',
    }),
  password: Joi.string().required().messages({
    'string.empty': 'Password wajib diisi',
  }),
});

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.replace('/');
    }
  }, [loading, isAuthenticated, router]);

  const {
    handleSubmit,
    control,
    formState: { isSubmitting, isValid },
  } = useForm<LoginForm>({
    resolver: joiResolver(loginSchema),
    mode: 'onChange',
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginForm) => {
    await login(data.email, data.password);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <div>
        <h2 className="font-display text-[28px] leading-[36px] text-[#251918]">
          Operator Login
        </h2>
        <p className="mt-1 text-sm text-[#58413F]">
          Masuk menggunakan akun operator BASARNAS yang terdaftar.
        </p>
      </div>

      <Controller
        name="email"
        control={control}
        render={({ field, fieldState }) => (
          <TextInput
            label="E-mail"
            variant="outlined"
            type="email"
            placeholder="ops@basarnas.go.id"
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
            placeholder="Masukkan password"
            {...field}
            error={fieldState.error?.message}
            disabled={isSubmitting}
          />
        )}
      />

      <Button
        type="submit"
        label={isSubmitting ? 'Memverifikasi...' : 'Log in'}
        variant="contained"
        color="primary"
        fullWidth
        className="h-12"
        disabled={!isValid || isSubmitting}
      />

      <div className="border-t border-[#DFBFBC] pt-4 text-center text-[13px] text-[#58413F]">
        Belum memiliki akun operator?{' '}
        <button
          type="button"
          onClick={() => router.push('/register')}
          className="font-bold text-[#7E1117] underline decoration-[#7E1117]/40 underline-offset-4 transition duration-150 hover:text-[#9F2B2B] cursor-pointer"
        >
          Daftar akun baru
        </button>
      </div>
    </form>
  );
}
