'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { formatTurkishDate } from '@/lib/dateUtils';
import Navigation from '@/components/Navigation';
import Breadcrumbs from '@/components/Breadcrumbs';
import { UserIcon, EmailIcon, RoleIcon, CalendarIcon, LockIcon, EditIcon, CheckIcon, XIcon } from '@/components/Icon';
import { themeColors, combineThemeClasses } from '@/lib/theme';

export default function ProfilePage() {
  const router = useRouter();
  const { isAuthenticated, isAuthLoading, logout } = useAuth();
  
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    username: '',
    email: ''
  });
  
  // Password change state
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [saving, setSaving] = useState(false);

  // Load profile
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.push('/login');
      return;
    }

    if (isAuthenticated) {
      loadProfile();
    }
  }, [isAuthenticated, isAuthLoading, router]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getMyProfile();
      setProfile(data);
      setEditForm({
        username: data.username,
        email: data.email
      });
    } catch (error) {
      console.error('Failed to load profile:', error);
      setError('Profil yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleEditToggle = () => {
    if (isEditing) {
      // Cancel edit - reset form
      setEditForm({
        username: profile.username,
        email: profile.email
      });
      setError('');
    }
    setIsEditing(!isEditing);
  };

  const handleSaveProfile = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');

      // Validate
      if (!editForm.username.trim()) {
        setError('Kullanıcı adı boş olamaz');
        return;
      }

      if (!editForm.email.trim()) {
        setError('E-posta adresi boş olamaz');
        return;
      }

      // Save
      const updatedProfile = await apiClient.updateMyProfile({
        username: editForm.username.trim(),
        email: editForm.email.trim()
      });

      // Update profile and localStorage
      setProfile(updatedProfile);
      const storedUser = localStorage.getItem('user');
      if (storedUser) {
        const userData = JSON.parse(storedUser);
        userData.username = updatedProfile.username;
        userData.email = updatedProfile.email;
        localStorage.setItem('user', JSON.stringify(userData));
      }

      setSuccess('Profil başarıyla güncellendi');
      setIsEditing(false);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (error: any) {
      console.error('Failed to update profile:', error);
      setError(error.response?.data?.detail || 'Profil güncellenirken hata oluştu');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');

      // Validate
      if (!passwordForm.current_password) {
        setError('Mevcut şifrenizi girin');
        return;
      }

      if (!passwordForm.new_password) {
        setError('Yeni şifrenizi girin');
        return;
      }

      if (passwordForm.new_password.length < 6) {
        setError('Yeni şifre en az 6 karakter olmalıdır');
        return;
      }

      if (passwordForm.new_password !== passwordForm.confirm_password) {
        setError('Yeni şifreler eşleşmiyor');
        return;
      }

      // Change password
      await apiClient.changeMyPassword({
        current_password: passwordForm.current_password,
        new_password: passwordForm.new_password
      });

      setSuccess('Şifre başarıyla değiştirildi');
      setShowPasswordModal(false);
      setPasswordForm({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(''), 3000);
    } catch (error: any) {
      console.error('Failed to change password:', error);
      setError(error.response?.data?.detail || 'Şifre değiştirirken hata oluştu');
    } finally {
      setSaving(false);
    }
  };

  if (isAuthLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className={combineThemeClasses('min-h-screen', themeColors.background.primary)}>
      <Navigation />
      
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumbs items={[
          { label: 'Ana Sayfa', href: '/' },
          { label: 'Profil', href: '/profile' }
        ]} />

        {/* Header */}
        <div className="mt-6 mb-8 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center">
              <span className="text-2xl font-bold text-indigo-600 dark:text-indigo-300">
                {profile?.username?.charAt(0)?.toUpperCase() || 'U'}
              </span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                Profil
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Hesap bilgilerinizi görüntüleyin ve güncelleyin
              </p>
            </div>
          </div>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div className="mb-6 bg-green-50 border-l-4 border-green-400 p-4 rounded-lg">
            <div className="flex">
              <CheckIcon size="md" className="text-green-400 mr-3" />
              <p className="text-green-800">{success}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-400 p-4 rounded-lg">
            <div className="flex">
              <XIcon size="md" className="text-red-400 mr-3" />
              <p className="text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Profile Information Card */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-gray-200 dark:border-slate-700 overflow-hidden mb-6">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-700 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <UserIcon size="md" className="mr-2" />
              Profil Bilgileri
            </h2>
            {!isEditing ? (
              <button
                onClick={handleEditToggle}
                className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 transition-colors flex items-center"
              >
                <EditIcon size="sm" className="mr-2" />
                Düzenle
              </button>
            ) : (
              <div className="flex space-x-2">
                <button
                  onClick={handleSaveProfile}
                  disabled={saving}
                  className="px-4 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 transition-colors flex items-center disabled:opacity-50"
                >
                  <CheckIcon size="sm" className="mr-2" />
                  {saving ? 'Kaydediliyor...' : 'Kaydet'}
                </button>
                <button
                  onClick={handleEditToggle}
                  disabled={saving}
                  className="px-4 py-2 bg-gray-500 text-white font-medium rounded-md hover:bg-gray-600 transition-colors flex items-center disabled:opacity-50"
                >
                  <XIcon size="sm" className="mr-2" />
                  İptal
                </button>
              </div>
            )}
          </div>

          <div className="p-6 space-y-6">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
                <UserIcon size="sm" className="mr-2" />
                Kullanıcı Adı
              </label>
              {isEditing ? (
                <input
                  type="text"
                  value={editForm.username}
                  onChange={(e) => setEditForm({ ...editForm, username: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-slate-700 dark:text-white"
                  placeholder="Kullanıcı adınız"
                />
              ) : (
                <p className="text-gray-900 dark:text-white text-lg">{profile?.username}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
                <EmailIcon size="sm" className="mr-2" />
                E-posta Adresi
              </label>
              {isEditing ? (
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-slate-700 dark:text-white"
                  placeholder="E-posta adresiniz"
                />
              ) : (
                <p className="text-gray-900 dark:text-white text-lg">{profile?.email}</p>
              )}
            </div>

            {/* Role (Read-only) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
                <RoleIcon size="sm" className="mr-2" />
                Rol
              </label>
              <div className="flex items-center space-x-2">
                <span className="px-3 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded-full text-sm font-medium">
                  {profile?.role_display_name}
                </span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  (Değiştirilemez)
                </span>
              </div>
            </div>

            {/* Created At */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
                <CalendarIcon size="sm" className="mr-2" />
                Kayıt Tarihi
              </label>
              <p className="text-gray-900 dark:text-white">
                {profile?.created_at ? formatTurkishDate(profile.created_at) : '-'}
              </p>
            </div>

            {/* Updated At */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center">
                <CalendarIcon size="sm" className="mr-2" />
                Son Güncelleme
              </label>
              <p className="text-gray-900 dark:text-white">
                {profile?.updated_at ? formatTurkishDate(profile.updated_at) : '-'}
              </p>
            </div>
          </div>
        </div>

        {/* Security Card */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-gray-200 dark:border-slate-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <LockIcon size="md" className="mr-2" />
              Güvenlik
            </h2>
          </div>

          <div className="p-6">
            <button
              onClick={() => setShowPasswordModal(true)}
              className="px-6 py-3 bg-gray-600 text-white font-medium rounded-md hover:bg-gray-700 transition-colors flex items-center"
            >
              <LockIcon size="sm" className="mr-2" />
              Şifre Değiştir
            </button>
          </div>
        </div>

        {/* Session Info */}
        <div className="mt-6 bg-gray-50 dark:bg-slate-800 rounded-lg p-4 border border-gray-200 dark:border-slate-700">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            💡 <strong>Oturum Bilgisi:</strong> 3 saat işlem yapmazsanız otomatik olarak çıkış yapılacaktır.
          </p>
        </div>
      </div>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-md w-full">
            <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <LockIcon size="md" className="mr-2" />
                Şifre Değiştir
              </h3>
            </div>

            <div className="p-6 space-y-4">
              {/* Error message in modal */}
              {error && (
                <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-400 p-4 rounded">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm text-red-800 dark:text-red-200 font-medium">{error}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Current Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Mevcut Şifre
                </label>
                <input
                  type="password"
                  value={passwordForm.current_password}
                  onChange={(e) => {
                    setPasswordForm({ ...passwordForm, current_password: e.target.value });
                    setError(''); // Clear error when typing
                  }}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-slate-700 dark:text-white"
                  placeholder="Mevcut şifreniz"
                />
              </div>

              {/* New Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Yeni Şifre
                </label>
                <input
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(e) => {
                    setPasswordForm({ ...passwordForm, new_password: e.target.value });
                    setError(''); // Clear error when typing
                  }}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-slate-700 dark:text-white"
                  placeholder="Yeni şifreniz (en az 6 karakter)"
                />
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Yeni Şifre (Tekrar)
                </label>
                <input
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={(e) => {
                    setPasswordForm({ ...passwordForm, confirm_password: e.target.value });
                    setError(''); // Clear error when typing
                  }}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-slate-700 dark:text-white"
                  placeholder="Yeni şifrenizi tekrar girin"
                />
              </div>

              {/* Password strength indicator */}
              {passwordForm.new_password && (
                <div className="text-sm">
                  <p className="text-gray-600 dark:text-gray-400 mb-1">Şifre Gücü:</p>
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 bg-gray-200 dark:bg-slate-600 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all ${
                          passwordForm.new_password.length < 6 ? 'w-1/3 bg-red-500' :
                          passwordForm.new_password.length < 8 ? 'w-2/3 bg-yellow-500' :
                          'w-full bg-green-500'
                        }`}
                      ></div>
                    </div>
                    <span className={`text-sm font-medium ${
                      passwordForm.new_password.length < 6 ? 'text-red-600' :
                      passwordForm.new_password.length < 8 ? 'text-yellow-600' :
                      'text-green-600'
                    }`}>
                      {passwordForm.new_password.length < 6 ? 'Zayıf' :
                       passwordForm.new_password.length < 8 ? 'Orta' :
                       'Güçlü'}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 py-4 bg-gray-50 dark:bg-slate-700 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowPasswordModal(false);
                  setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
                  setError('');
                }}
                disabled={saving}
                className="px-4 py-2 bg-gray-500 text-white font-medium rounded-md hover:bg-gray-600 transition-colors disabled:opacity-50"
              >
                İptal
              </button>
              <button
                onClick={handleChangePassword}
                disabled={saving}
                className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center"
              >
                <CheckIcon size="sm" className="mr-2" />
                {saving ? 'Değiştiriliyor...' : 'Şifreyi Değiştir'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

