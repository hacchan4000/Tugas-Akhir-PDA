'use client';

import React from 'react';
import {
  MdAnalytics,
  MdHistory,
  MdLogout,
  MdOutlineShield,
  MdRadar,
  MdRefresh,
} from 'react-icons/md';
import Button from '@/app/components/atoms/Button';
import { useAuth } from '@/hooks/useAuth';
import { useHist } from '@/hooks/useHist';
import { cn } from '@/utils/classNames';

export type WorkspaceTab = 'predict' | 'history' | 'model';

interface TopNavbarProps {
  activeTab: WorkspaceTab;
  onChangeTab: (tab: WorkspaceTab) => void;
}

const TABS: Array<{ id: WorkspaceTab; label: string; icon: React.ReactNode }> = [
  { id: 'predict', label: 'Prediksi & SAR', icon: <MdRadar className="text-lg" /> },
  { id: 'history', label: 'Riwayat & Ekspor', icon: <MdHistory className="text-lg" /> },
  { id: 'model', label: 'Info Model', icon: <MdAnalytics className="text-lg" /> },
];

export function TopNavbar({ activeTab, onChangeTab }: TopNavbarProps) {
  const { user, logout } = useAuth();
  const { health, refreshHealth } = useHist();

  const isHealthy = health?.status === 'ok' && health?.model_ready;

  return (
    <header className="sticky top-0 z-30 border-b border-[#DFBFBC] bg-[#FFFFFF]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:px-8 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="flex h-11 w-11 items-center justify-center rounded-[12px] bg-[#7E1117] text-white shadow-sm">
              <MdOutlineShield className="text-2xl" />
            </div>
            <div>
              <h1 className="font-display text-xl font-normal tracking-[-0.25px] text-[#251918] sm:text-2xl">
                Klasifikasi Landslide
              </h1>
              <p className="text-[13px] text-[#58413F]">
                Analisis Bahaya Geospasial &amp; Prioritas Penanganan SAR
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => void refreshHealth()}
            title={
              health?.model_error
                ? health.model_error
                : `API: ${health?.status ?? 'checking'}, DB: ${health?.database ?? '-'}`
            }
            className={cn(
              'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold transition duration-150 ease-[cubic-bezier(0.2,0,0,1)] lg:hidden',
              isHealthy
                ? 'bg-[#ABECDE]/60 text-[#26695E] border border-[#26695E]/30'
                : 'bg-[#FFDAD6] text-[#93000A] border border-[#BA1A1A]/30'
            )}
          >
            <span
              className={cn(
                'h-2 w-2 rounded-full',
                isHealthy ? 'bg-[#26695E]' : 'bg-[#BA1A1A]'
              )}
            />
            {isHealthy ? `Model ${health?.model_version ?? ''}` : 'Cek Status'}
          </button>
        </div>

        <nav className="flex flex-wrap items-center gap-1 rounded-[16px] border border-[#DFBFBC] bg-[#FFF0EF] p-1">
          {TABS.map((tab) => {
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onChangeTab(tab.id)}
                className={cn(
                  'flex items-center gap-2 rounded-[12px] px-4 py-2 text-sm font-bold transition duration-150 ease-[cubic-bezier(0.2,0,0,1)] cursor-pointer',
                  active
                    ? 'bg-[#7E1117] text-white shadow-sm'
                    : 'text-[#58413F] hover:bg-white/80 hover:text-[#251918]'
                )}
              >
                {tab.icon}
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="flex items-center justify-between gap-3 lg:justify-end">
          <button
            type="button"
            onClick={() => void refreshHealth()}
            title={
              health?.model_error
                ? health.model_error
                : `Status API: ${health?.status ?? 'checking'} | DB: ${health?.database ?? '-'}`
            }
            className={cn(
              'hidden lg:inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-xs font-bold transition duration-150 ease-[cubic-bezier(0.2,0,0,1)] hover:opacity-90 cursor-pointer',
              isHealthy
                ? 'bg-[#ABECDE]/55 text-[#26695E] border border-[#26695E]/30'
                : 'bg-[#FFDAD6] text-[#93000A] border border-[#BA1A1A]/30'
            )}
          >
            <span
              className={cn(
                'h-2 w-2 rounded-full',
                isHealthy ? 'bg-[#26695E]' : 'bg-[#BA1A1A]'
              )}
            />
            <span>
              {isHealthy
                ? `Model ${health?.model_version ?? 'v1'} Siap`
                : health?.status === 'offline'
                  ? 'API Offline'
                  : 'Model Belum Siap'}
            </span>
            <MdRefresh className="text-sm opacity-75" />
          </button>

          {user && (
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-xs font-bold text-[#251918]">{user.name}</p>
                <p className="text-[11px] text-[#58413F]">{user.email}</p>
              </div>
              <Button
                label="Log out"
                variant="outlined"
                color="secondary"
                prefix={<MdLogout />}
                onClick={() => void logout()}
                className="px-3.5 py-1.5 text-xs"
              />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
