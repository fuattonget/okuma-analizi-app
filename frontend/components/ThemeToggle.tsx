'use client';

import React from 'react';
import { useTheme } from '@/lib/useTheme';
import { themeColors, combineThemeClasses } from '@/lib/theme';
import Icon from './Icon';

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const cycleTheme = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('system');
    } else {
      setTheme('light');
    }
  };

  const getThemeIcon = () => {
    if (theme === 'system') {
      return '🖥️'; // System icon
    }
    return resolvedTheme === 'dark' ? '🌙' : '☀️';
  };

  const getThemeLabel = () => {
    if (theme === 'system') {
      return 'Sistem';
    }
    return resolvedTheme === 'dark' ? 'Karanlık' : 'Aydınlık';
  };

  return (
    <button
      onClick={cycleTheme}
      className={combineThemeClasses(
        'flex items-center space-x-2 px-3 py-2 rounded-lg transition-all duration-200',
        themeColors.background.hover,
        themeColors.shadow.sm,
        'hover:shadow-md'
      )}
      title={`Tema: ${getThemeLabel()}`}
    >
      <span className="text-lg">{getThemeIcon()}</span>
      <span className={combineThemeClasses(
        'text-sm font-medium',
        themeColors.text.secondary
      )}>
        {getThemeLabel()}
      </span>
    </button>
  );
}
