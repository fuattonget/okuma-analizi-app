/**
 * Light & Dark Mode Color Standards
 * Bu dosya tüm uygulamada kullanılacak standart light ve dark mode renklerini tanımlar
 */

export const themeColors = {
  // Background Colors - Aydınlık mod için çok daha açık renkler
  background: {
    primary: 'bg-white dark:bg-slate-800',                    // Ana arka plan (kartlar, modaller)
    secondary: 'bg-gray-50 dark:bg-slate-900',               // Sayfa arka planı - çok daha açık
    tertiary: 'bg-gray-100 dark:bg-slate-700',               // Alt arka planlar - daha açık
    quaternary: 'bg-gray-200 dark:bg-slate-600',             // Daha açık alt arka planlar
    hover: 'hover:bg-gray-50 dark:hover:bg-slate-700/50',   // Hover efektleri - çok hafif
    hoverLight: 'hover:bg-gray-100 dark:hover:bg-slate-700/50', // Daha belirgin hover
  },
  
  // Text Colors - Aydınlık mod için daha kontrastlı
  text: {
    primary: 'text-slate-900 dark:text-slate-100',           // Ana metin - daha koyu
    secondary: 'text-slate-700 dark:text-slate-300',         // İkincil metin
    tertiary: 'text-slate-600 dark:text-slate-400',          // Üçüncül metin - daha koyu
    muted: 'text-slate-500 dark:text-slate-500',             // Soluk metin
    inverse: 'text-white dark:text-slate-900',               // Ters renk metin
    accent: 'text-indigo-600 dark:text-indigo-400',          // Vurgu metni
  },
  
  // Border Colors - Aydınlık mod için daha ince ve zarif
  border: {
    primary: 'border-slate-200 dark:border-slate-600',       // Ana border - daha ince
    secondary: 'border-slate-300 dark:border-slate-500',     // İkincil border
    subtle: 'border-slate-100 dark:border-slate-700',        // Çok ince border
    focus: 'border-indigo-500 dark:border-indigo-400',       // Focus border
    error: 'border-red-500 dark:border-red-400',             // Hata border
    success: 'border-green-500 dark:border-green-400',       // Başarı border
  },
  
  // Input Colors - Aydınlık mod için daha temiz
  input: {
    background: 'bg-white dark:bg-slate-700',
    text: 'text-slate-900 dark:text-slate-100',
    placeholder: 'placeholder-slate-500 dark:placeholder-slate-400',
    border: 'border-slate-300 dark:border-slate-600',
    focus: 'focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400',
    hover: 'hover:border-slate-400 dark:hover:border-slate-500',
  },
  
  // Button Colors - Aydınlık mod için daha modern
  button: {
    primary: 'bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-600 dark:hover:bg-indigo-700 text-white shadow-sm hover:shadow-md',
    secondary: 'bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-600',
    danger: 'bg-red-600 hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700 text-white shadow-sm hover:shadow-md',
    success: 'bg-green-600 hover:bg-green-700 dark:bg-green-600 dark:hover:bg-green-700 text-white shadow-sm hover:shadow-md',
    ghost: 'bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300',
  },
  
  // Status Colors - Aydınlık mod için daha yumuşak
  status: {
    success: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800',
    error: 'bg-red-50 text-red-700 dark:bg-red-900/30 dark:text-red-300 border border-red-200 dark:border-red-800',
    warning: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300 border border-amber-200 dark:border-amber-800',
    info: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border border-blue-200 dark:border-blue-800',
  },
  
  // Shadow Colors - Aydınlık mod için daha yumuşak gölgeler
  shadow: {
    sm: 'shadow-sm dark:shadow-slate-900/25',
    md: 'shadow-md dark:shadow-slate-900/25',
    lg: 'shadow-lg dark:shadow-slate-900/25',
    xl: 'shadow-xl dark:shadow-slate-900/25',
    inner: 'shadow-inner dark:shadow-slate-900/25',
    none: 'shadow-none',
  },
  
  // Gradient Colors - Aydınlık mod için gradient efektler
  gradient: {
    primary: 'bg-gradient-to-r from-indigo-500 to-purple-600 dark:from-indigo-600 dark:to-purple-700',
    secondary: 'bg-gradient-to-r from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-700',
    subtle: 'bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800',
  }
} as const;

/**
 * Utility function to combine multiple theme classes
 */
export function combineThemeClasses(...classes: string[]): string {
  return classes.filter(Boolean).join(' ');
}

/**
 * Common component class combinations
 */
export const componentClasses = {
  card: combineThemeClasses(
    themeColors.background.primary,
    themeColors.border.primary,
    themeColors.shadow.md,
    'rounded-xl border transition-all duration-200 hover:shadow-lg'
  ),
  
  cardSubtle: combineThemeClasses(
    themeColors.background.primary,
    themeColors.border.subtle,
    themeColors.shadow.sm,
    'rounded-lg border transition-all duration-200'
  ),
  
  input: combineThemeClasses(
    themeColors.input.background,
    themeColors.input.text,
    themeColors.input.border,
    themeColors.input.focus,
    themeColors.input.hover,
    'px-3 py-2 rounded-lg focus:outline-none focus:ring-2 transition-all duration-200'
  ),
  
  button: {
    primary: combineThemeClasses(
      themeColors.button.primary,
      'px-4 py-2 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2'
    ),
    secondary: combineThemeClasses(
      themeColors.button.secondary,
      'px-4 py-2 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2'
    ),
    ghost: combineThemeClasses(
      themeColors.button.ghost,
      'px-4 py-2 rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2'
    ),
  },
  
  table: {
    container: combineThemeClasses(
      themeColors.background.primary,
      themeColors.border.primary,
      themeColors.shadow.sm,
      'rounded-xl border overflow-hidden'
    ),
    header: combineThemeClasses(
      'bg-slate-50 dark:bg-slate-700',
      'text-xs font-semibold uppercase tracking-wider',
      themeColors.text.secondary
    ),
    row: combineThemeClasses(
      themeColors.background.primary,
      themeColors.hoverLight,
      'transition-colors duration-200 border-b border-slate-100 dark:border-slate-700'
    ),
    cell: combineThemeClasses(
      'px-6 py-4 whitespace-nowrap text-sm',
      themeColors.text.primary
    ),
  },
  
  modal: combineThemeClasses(
    themeColors.background.primary,
    themeColors.border.primary,
    themeColors.shadow.xl,
    'rounded-2xl border max-w-md w-full mx-4'
  ),
  
  badge: {
    success: combineThemeClasses(
      themeColors.status.success,
      'px-2 py-1 rounded-full text-xs font-medium'
    ),
    error: combineThemeClasses(
      themeColors.status.error,
      'px-2 py-1 rounded-full text-xs font-medium'
    ),
    warning: combineThemeClasses(
      themeColors.status.warning,
      'px-2 py-1 rounded-full text-xs font-medium'
    ),
    info: combineThemeClasses(
      themeColors.status.info,
      'px-2 py-1 rounded-full text-xs font-medium'
    ),
  }
} as const;
