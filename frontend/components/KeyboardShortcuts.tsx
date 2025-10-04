'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/lib/useAuth';
import { useTheme } from '@/lib/useTheme';
import classNames from 'classnames';

interface Shortcut {
  key: string;
  description: string;
  action: () => void;
  category?: string;
}

interface KeyboardShortcutsProps {
  shortcuts?: Shortcut[];
  showHelp?: boolean;
  className?: string;
  global?: boolean;
}

export default function KeyboardShortcuts({ 
  shortcuts = [], 
  showHelp = false, 
  className,
  global = false
}: KeyboardShortcutsProps) {
  const [showShortcuts, setShowShortcuts] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();
  const { theme, setTheme } = useTheme();

  // Global shortcuts that work on all pages
  const globalShortcuts: Shortcut[] = [
    {
      key: 'Ctrl+K',
      description: 'Klavye kısayollarını göster/gizle',
      action: () => setShowShortcuts(!showShortcuts),
      category: 'Genel'
    },
    {
      key: 'Ctrl+1',
      description: 'Ana sayfaya git',
      action: () => router.push('/'),
      category: 'Navigasyon'
    },
    {
      key: 'Ctrl+2',
      description: 'Geçmiş analizlere git',
      action: () => router.push('/analyses'),
      category: 'Navigasyon'
    },
    {
      key: 'Ctrl+3',
      description: 'Metin yönetimine git',
      action: () => router.push('/texts'),
      category: 'Navigasyon'
    },
    {
      key: 'Ctrl+4',
      description: 'Öğrenci yönetimine git',
      action: () => router.push('/students'),
      category: 'Navigasyon'
    },
    {
      key: 'Escape',
      description: 'Modal\'ları kapat',
      action: () => setShowShortcuts(false),
      category: 'Genel'
    },
    {
      key: 'Ctrl+D',
      description: 'Tema değiştir',
      action: () => {
        if (theme === 'light') {
          setTheme('dark');
        } else if (theme === 'dark') {
          setTheme('system');
        } else {
          setTheme('light');
        }
      },
      category: 'Genel'
    }
  ];

  // Use global shortcuts if global=true, otherwise use provided shortcuts
  const activeShortcuts = global ? globalShortcuts : shortcuts;

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if user is typing in an input, textarea, or contenteditable
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.contentEditable === 'true' ||
        target.isContentEditable
      ) {
        return;
      }

      // Only work if user is authenticated (for global shortcuts)
      if (global && !isAuthenticated) {
        return;
      }

      // Find matching shortcut
      const matchingShortcut = activeShortcuts.find(shortcut => {
        const keys = shortcut.key.toLowerCase().split('+').map(k => k.trim());
        
        // Check modifier keys
        const hasCtrl = keys.includes('ctrl') && (event.ctrlKey || event.metaKey);
        const hasAlt = keys.includes('alt') && event.altKey;
        const hasShift = keys.includes('shift') && event.shiftKey;
        
        // Check main key
        const mainKey = keys.find(k => !['ctrl', 'alt', 'shift', 'cmd'].includes(k));
        const keyMatches = mainKey === event.key.toLowerCase() || 
                          (mainKey === 'enter' && event.key === 'Enter') ||
                          (mainKey === 'space' && event.key === ' ') ||
                          (mainKey === 'escape' && event.key === 'Escape') ||
                          (mainKey === 'tab' && event.key === 'Tab');

        // Check if all required modifiers are present
        const requiredModifiers = keys.filter(k => ['ctrl', 'alt', 'shift', 'cmd'].includes(k));
        const hasAllModifiers = requiredModifiers.every(mod => {
          if (mod === 'ctrl') return event.ctrlKey || event.metaKey;
          if (mod === 'alt') return event.altKey;
          if (mod === 'shift') return event.shiftKey;
          if (mod === 'cmd') return event.metaKey;
          return false;
        });

        return keyMatches && hasAllModifiers;
      });

      if (matchingShortcut) {
        event.preventDefault();
        matchingShortcut.action();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [activeShortcuts, global, isAuthenticated]);

  if (!showShortcuts) return null;

  const groupedShortcuts = activeShortcuts.reduce((acc, shortcut) => {
    const category = shortcut.category || 'Genel';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(shortcut);
    return acc;
  }, {} as Record<string, Shortcut[]>);

  return (
    <>
      {/* Shortcuts Help Modal */}
      {showShortcuts && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Klavye Kısayolları
                </h2>
                <button
                  onClick={() => setShowShortcuts(false)}
                  className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <span className="text-2xl">✕</span>
                </button>
              </div>

              <div className="space-y-6">
                {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => (
                  <div key={category}>
                    <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-3">
                      {category}
                    </h3>
                    <div className="space-y-2">
                      {categoryShortcuts.map((shortcut, index) => (
                        <div
                          key={index}
                          className="flex justify-between items-center py-2 px-3 bg-gray-50 dark:bg-gray-700 rounded-md"
                        >
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {shortcut.description}
                          </span>
                          <div className="flex space-x-1">
                            {shortcut.key.split('+').map((key, keyIndex) => (
                              <React.Fragment key={keyIndex}>
                                <kbd className="px-2 py-1 text-xs font-mono bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded shadow-sm text-gray-800 dark:text-gray-200">
                                  {key.trim()}
                                </kbd>
                                {keyIndex < shortcut.key.split('+').length - 1 && (
                                  <span className="text-gray-400 dark:text-gray-500">+</span>
                                )}
                              </React.Fragment>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-600">
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
                  <kbd className="px-2 py-1 text-xs font-mono bg-gray-100 dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-gray-800 dark:text-gray-200">
                    Ctrl
                  </kbd>
                  <span className="mx-1">+</span>
                  <kbd className="px-2 py-1 text-xs font-mono bg-gray-100 dark:bg-gray-600 border border-gray-300 dark:border-gray-500 rounded text-gray-800 dark:text-gray-200">
                    K
                  </kbd>
                  <span className="ml-2">ile bu yardımı açıp kapatabilirsiniz</span>
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Hook for using keyboard shortcuts
export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Ignore if user is typing in an input, textarea, or contenteditable
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.contentEditable === 'true' ||
        target.isContentEditable
      ) {
        return;
      }

      // Find matching shortcut
      const matchingShortcut = shortcuts.find(shortcut => {
        const keys = shortcut.key.toLowerCase().split('+').map(k => k.trim());
        
        // Check modifier keys
        const hasCtrl = keys.includes('ctrl') && (event.ctrlKey || event.metaKey);
        const hasAlt = keys.includes('alt') && event.altKey;
        const hasShift = keys.includes('shift') && event.shiftKey;
        
        // Check main key
        const mainKey = keys.find(k => !['ctrl', 'alt', 'shift', 'cmd'].includes(k));
        const keyMatches = mainKey === event.key.toLowerCase() || 
                          (mainKey === 'enter' && event.key === 'Enter') ||
                          (mainKey === 'space' && event.key === ' ') ||
                          (mainKey === 'escape' && event.key === 'Escape') ||
                          (mainKey === 'tab' && event.key === 'Tab');

        // Check if all required modifiers are present
        const requiredModifiers = keys.filter(k => ['ctrl', 'alt', 'shift', 'cmd'].includes(k));
        const hasAllModifiers = requiredModifiers.every(mod => {
          if (mod === 'ctrl') return event.ctrlKey || event.metaKey;
          if (mod === 'alt') return event.altKey;
          if (mod === 'shift') return event.shiftKey;
          if (mod === 'cmd') return event.metaKey;
          return false;
        });

        return keyMatches && hasAllModifiers;
      });

      if (matchingShortcut) {
        event.preventDefault();
        matchingShortcut.action();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}
