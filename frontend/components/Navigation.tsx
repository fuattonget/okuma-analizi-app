'use client';

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import classNames from 'classnames';
import { useAuth } from '@/lib/useAuth';
import { useRoles } from '@/lib/useRoles';
import { HomeIcon, AnalysesIcon, TextsIcon, StudentsIcon, MenuIcon, LogoutIcon, SettingsIcon } from '@/components/Icon';
import { ThemeToggle } from '@/components/ThemeToggle';
import { themeColors, combineThemeClasses } from '@/lib/theme';

export default function Navigation() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();
  const { logout, isAuthenticated } = useAuth();
  const { currentUser, hasPermission, getRoleDisplayName, getRoleColor } = useRoles();

  const menuItems = [
    { href: '/', label: 'Ana Sayfa', icon: HomeIcon, permission: null },
    { href: '/analyses', label: 'Geçmiş Analizler', icon: AnalysesIcon, permission: 'analyses_access' },
    { href: '/texts', label: 'Metin Yönetimi', icon: TextsIcon, permission: 'texts_access' },
    { href: '/students', label: 'Öğrenci Yönetimi', icon: StudentsIcon, permission: 'students_access' },
    { href: '/settings', label: 'Sistem Ayarları', icon: SettingsIcon, permission: 'settings_access' },
  ];
  
  // Custom permission checks for menu items
  const canAccessSettings = () => {
    return hasPermission('user_management' as any) || 
           hasPermission('role_management' as any) ||
           hasPermission('user:read' as any) ||
           hasPermission('role:read' as any);
  };
  
  const canAccessStudents = () => {
    return hasPermission('student_management' as any) ||
           hasPermission('student:read' as any) ||
           hasPermission('student:view' as any);
  };
  
  const canAccessTexts = () => {
    return hasPermission('text_management' as any) ||
           hasPermission('text:read' as any) ||
           hasPermission('text:view' as any);
  };
  
  const canAccessAnalyses = () => {
    return hasPermission('analysis_management' as any) ||
           hasPermission('analysis:read' as any) ||
           hasPermission('analysis:view' as any);
  };

  // Filter menu items based on permissions
  const filteredMenuItems = menuItems.filter(item => {
    if (!item.permission) return true;
    if (item.permission === 'settings_access') return canAccessSettings();
    if (item.permission === 'students_access') return canAccessStudents();
    if (item.permission === 'texts_access') return canAccessTexts();
    if (item.permission === 'analyses_access') return canAccessAnalyses();
    return hasPermission(item.permission as keyof import('@/lib/useRoles').Permission);
  });
  
  const currentItem = filteredMenuItems.find(item => item.href === pathname);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.navigation-menu')) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div className={combineThemeClasses(
      themeColors.background.primary,
      themeColors.shadow.sm,
      themeColors.border.primary,
      'border-b'
    )}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          {/* Left side - Navigation and App title */}
          <div className="flex items-center space-x-6">
            {/* Navigation Menu */}
            <div className="relative navigation-menu">
              {/* Hamburger Button */}
              <button
                onClick={() => setIsOpen(!isOpen)}
                className={combineThemeClasses(
                  'p-2 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-all duration-200',
                  themeColors.text.secondary,
                  'hover:text-gray-900 dark:hover:text-slate-100',
                  themeColors.background.hover
                )}
                aria-label="Menüyü aç/kapat"
              >
                <MenuIcon size="lg" />
              </button>

              {/* Dropdown Menu */}
              {isOpen && (
                <div className={combineThemeClasses(
                  'absolute left-0 top-full mt-2 w-64 rounded-lg shadow-lg border z-50 backdrop-blur-sm dark:backdrop-blur-md',
                  themeColors.background.primary,
                  themeColors.border.primary
                )}>
                  <div className="py-2">
                    <div className={combineThemeClasses(
                      'px-4 py-2 text-xs font-semibold uppercase tracking-wider border-b',
                      themeColors.text.tertiary,
                      'border-gray-100 dark:border-slate-600'
                    )}>
                      Sayfa Seçimi
                    </div>
                    
                    {filteredMenuItems.map((item) => (
                      <a
                        key={item.href}
                        href={item.href}
                        onClick={() => setIsOpen(false)}
                        className={classNames(
                          'flex items-center px-4 py-3 text-sm transition-all duration-200',
                          pathname === item.href
                            ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-r-2 border-blue-700 dark:border-blue-400'
                            : combineThemeClasses(
                                themeColors.text.secondary,
                                themeColors.background.hover
                              )
                        )}
                      >
                        <span className="mr-3">
                          {item.icon({ size: "md" })}
                        </span>
                        <span className="font-medium">{item.label}</span>
                        {pathname === item.href && (
                          <span className="ml-auto text-blue-600 dark:text-blue-400">
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path
                                fillRule="evenodd"
                                d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                clipRule="evenodd"
                              />
                            </svg>
                          </span>
                        )}
                      </a>
                    ))}

                    {/* User Info */}
                    {isAuthenticated && currentUser && currentUser.username && (
                      <>
                        <div className="border-t border-gray-100 dark:border-slate-600 my-2"></div>
                        <div className="px-4 py-3">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center">
                              <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-300">
                                {currentUser.username.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 dark:text-slate-100 truncate">
                                {currentUser.username}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-slate-400 truncate">
                                {currentUser.email}
                              </p>
                              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium mt-1 ${getRoleColor(currentUser.role)}`}>
                                {getRoleDisplayName(currentUser.role)}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="border-t border-gray-100 dark:border-slate-600 my-2"></div>
                        <button
                          onClick={() => {
                            logout();
                            setIsOpen(false);
                          }}
                          className="flex items-center w-full px-4 py-3 text-sm text-red-700 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-200"
                        >
                          <span className="mr-3">
                            <LogoutIcon size="md" />
                          </span>
                          <span className="font-medium">Çıkış Yap</span>
                        </button>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* App title */}
            <div>
              <h1 className={combineThemeClasses(
                'text-3xl font-bold flex items-center',
                themeColors.text.primary
              )}>
                <span className="text-3xl mr-3">📚</span>
                Okuma Analizi
              </h1>
              <p className={combineThemeClasses(
                'mt-1 text-sm',
                themeColors.text.tertiary
              )}>
                Ses dosyası yükleyin ve okuma analizi yapın
              </p>
            </div>
          </div>

          {/* Right side - Theme toggle and Page title */}
          <div className="flex items-center space-x-4">
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* Current page title */}
            {currentItem && (
              <div className="hidden md:block text-right">
                <h2 className={combineThemeClasses(
                  'text-xl font-semibold flex items-center',
                  themeColors.text.primary
                )}>
                  <span className="text-2xl mr-2">{currentItem.icon}</span>
                  {currentItem.label}
                </h2>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}