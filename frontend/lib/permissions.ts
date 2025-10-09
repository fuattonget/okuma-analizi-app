// Permission grupları ve Türkçe çevirileri
import { ComponentType } from 'react';

export interface PermissionInfo {
  key: string;
  label: string;
  description: string;
}

export interface PermissionGroup {
  id: string;
  label: string;
  icon: string; // Icon component name
  color: string;
  permissions: PermissionInfo[];
}

export const PERMISSION_GROUPS: PermissionGroup[] = [
  {
    id: 'student',
    label: 'Öğrenci Yönetimi',
    icon: 'StudentsIcon',
    color: 'blue',
    permissions: [
      {
        key: 'student:create',
        label: 'Öğrenci Oluştur',
        description: 'Yeni öğrenci ekleyebilir'
      },
      {
        key: 'student:read',
        label: 'Öğrenci Listele',
        description: 'Öğrenci listesini görüntüleyebilir'
      },
      {
        key: 'student:view',
        label: 'Öğrenci Detay',
        description: 'Öğrenci detaylarını görüntüleyebilir'
      },
      {
        key: 'student:update',
        label: 'Öğrenci Güncelle',
        description: 'Öğrenci bilgilerini düzenleyebilir'
      },
      {
        key: 'student:delete',
        label: 'Öğrenci Sil',
        description: 'Öğrenciyi silebilir veya pasif edebilir'
      }
    ]
  },
  {
    id: 'text',
    label: 'Metin Yönetimi',
    icon: 'TextsIcon',
    color: 'green',
    permissions: [
      {
        key: 'text:create',
        label: 'Metin Oluştur',
        description: 'Yeni metin ekleyebilir'
      },
      {
        key: 'text:read',
        label: 'Metin Listele',
        description: 'Metin listesini görüntüleyebilir'
      },
      {
        key: 'text:view',
        label: 'Metin Detay',
        description: 'Metin detaylarını görüntüleyebilir'
      },
      {
        key: 'text:update',
        label: 'Metin Güncelle',
        description: 'Metin içeriğini düzenleyebilir'
      },
      {
        key: 'text:delete',
        label: 'Metin Sil',
        description: 'Metni silebilir'
      }
    ]
  },
  {
    id: 'analysis',
    label: 'Analiz Yönetimi',
    icon: 'AnalysesIcon',
    color: 'purple',
    permissions: [
      {
        key: 'analysis:create',
        label: 'Analiz Oluştur',
        description: 'Yeni analiz başlatabilir'
      },
      {
        key: 'analysis:read',
        label: 'Öğrenci Analizlerini Görüntüle',
        description: 'Öğrenci detay sayfasında analizleri görüntüleyebilir'
      },
      {
        key: 'analysis:read_all',
        label: 'Tüm Analizleri Görüntüle',
        description: 'Analizler sayfasında tüm analizleri görüntüleyebilir'
      },
      {
        key: 'analysis:view',
        label: 'Analiz Detay',
        description: 'Analiz sonuçlarını görüntüleyebilir'
      },
      {
        key: 'analysis:update',
        label: 'Analiz Güncelle',
        description: 'Analiz bilgilerini düzenleyebilir'
      },
      {
        key: 'analysis:delete',
        label: 'Analiz Sil',
        description: 'Analizi silebilir'
      }
    ]
  },
  {
    id: 'user',
    label: 'Kullanıcı Yönetimi',
    icon: 'UserIcon',
    color: 'yellow',
    permissions: [
      {
        key: 'user:create',
        label: 'Kullanıcı Oluştur',
        description: 'Yeni kullanıcı ekleyebilir'
      },
      {
        key: 'user:read',
        label: 'Kullanıcı Listele',
        description: 'Kullanıcı listesini görüntüleyebilir'
      },
      {
        key: 'user:view',
        label: 'Kullanıcı Detay',
        description: 'Kullanıcı detaylarını görüntüleyebilir'
      },
      {
        key: 'user:update',
        label: 'Kullanıcı Güncelle',
        description: 'Kullanıcı bilgilerini düzenleyebilir'
      },
      {
        key: 'user:delete',
        label: 'Kullanıcı Sil',
        description: 'Kullanıcıyı silebilir'
      }
    ]
  },
  {
    id: 'role',
    label: 'Rol Yönetimi',
    icon: 'ShieldIcon',
    color: 'red',
    permissions: [
      {
        key: 'role:create',
        label: 'Rol Oluştur',
        description: 'Yeni rol ekleyebilir'
      },
      {
        key: 'role:read',
        label: 'Rol Listele',
        description: 'Rol listesini görüntüleyebilir'
      },
      {
        key: 'role:view',
        label: 'Rol Detay',
        description: 'Rol detaylarını görüntüleyebilir'
      },
      {
        key: 'role:update',
        label: 'Rol Güncelle',
        description: 'Rol yetkilerini düzenleyebilir'
      },
      {
        key: 'role:delete',
        label: 'Rol Sil',
        description: 'Rolü silebilir'
      }
    ]
  },
  {
    id: 'system',
    label: 'Sistem Yönetimi',
    icon: 'SettingsIcon',
    color: 'gray',
    permissions: [
      {
        key: 'system:settings',
        label: 'Sistem Ayarları',
        description: 'Sistem ayarlarına erişebilir'
      },
      {
        key: 'system:logs',
        label: 'Sistem Logları',
        description: 'Sistem loglarını görüntüleyebilir'
      },
      {
        key: 'system:status',
        label: 'Sistem Durumu',
        description: 'Sistem durumunu izleyebilir'
      }
    ]
  }
];

// Permission key'den label'a çeviri fonksiyonu
export function getPermissionLabel(key: string): string {
  for (const group of PERMISSION_GROUPS) {
    const permission = group.permissions.find(p => p.key === key);
    if (permission) {
      return permission.label;
    }
  }
  return key; // Bulunamazsa key'i döndür
}

// Permission key'den description'a çeviri fonksiyonu
export function getPermissionDescription(key: string): string {
  for (const group of PERMISSION_GROUPS) {
    const permission = group.permissions.find(p => p.key === key);
    if (permission) {
      return permission.description;
    }
  }
  return '';
}

// Icon name'den component'e mapping
export function getIconComponent(iconName: string): any {
  const iconMap: Record<string, string> = {
    'StudentsIcon': 'StudentsIcon',
    'TextsIcon': 'TextsIcon',
    'AnalysesIcon': 'AnalysesIcon',
    'UserIcon': 'UserIcon',
    'ShieldIcon': 'ShieldIcon',
    'SettingsIcon': 'SettingsIcon'
  };
  return iconMap[iconName] || 'ShieldIcon';
}

// Grup renklerini tanımla
export const GROUP_COLORS = {
  blue: {
    bg: 'bg-blue-50 dark:bg-blue-900/30',
    border: 'border-blue-200 dark:border-blue-700',
    text: 'text-blue-900 dark:text-blue-200',
    badge: 'bg-blue-100 text-blue-800 dark:bg-blue-600 dark:text-white'
  },
  green: {
    bg: 'bg-green-50 dark:bg-green-900/30',
    border: 'border-green-200 dark:border-green-700',
    text: 'text-green-900 dark:text-green-200',
    badge: 'bg-green-100 text-green-800 dark:bg-green-600 dark:text-white'
  },
  purple: {
    bg: 'bg-purple-50 dark:bg-purple-900/30',
    border: 'border-purple-200 dark:border-purple-700',
    text: 'text-purple-900 dark:text-purple-200',
    badge: 'bg-purple-100 text-purple-800 dark:bg-purple-700 dark:text-white'
  },
  yellow: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/30',
    border: 'border-yellow-200 dark:border-yellow-700',
    text: 'text-yellow-900 dark:text-yellow-200',
    badge: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-600 dark:text-white'
  },
  red: {
    bg: 'bg-red-50 dark:bg-red-900/30',
    border: 'border-red-200 dark:border-red-700',
    text: 'text-red-900 dark:text-red-200',
    badge: 'bg-red-100 text-red-800 dark:bg-red-600 dark:text-white'
  },
  gray: {
    bg: 'bg-gray-50 dark:bg-gray-800/40',
    border: 'border-gray-200 dark:border-gray-600',
    text: 'text-gray-900 dark:text-gray-200',
    badge: 'bg-gray-100 text-gray-800 dark:bg-gray-600 dark:text-white'
  }
};

