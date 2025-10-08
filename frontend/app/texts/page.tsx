'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, Text } from '@/lib/api';
import { formatTurkishDate } from '@/lib/dateUtils';
import { useAuth } from '@/lib/useAuth';
import { useRoles } from '@/lib/useRoles';
import classNames from 'classnames';
import Navigation from '@/components/Navigation';
import { themeColors, combineThemeClasses, componentClasses } from '@/lib/theme';

export default function TextsPage() {
  const router = useRouter();
  const { isAuthenticated, isAuthLoading } = useAuth();
  const { hasPermission } = useRoles();
  
  const [texts, setTexts] = useState<Text[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingText, setEditingText] = useState<Text | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    grade: '',
    body: ''
  });
  const [formErrors, setFormErrors] = useState({
    title: '',
    grade: '',
    body: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Handle token expiration and redirect
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      console.log('🔍 TextsPage: User not authenticated, redirecting to login');
      router.push('/login');
    }
  }, [isAuthenticated, isAuthLoading, router]);

  // Load texts when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadTexts();
    }
  }, [isAuthenticated]);

  const loadTexts = useCallback(async () => {
    try {
      setLoading(true);
      const textsData = await apiClient.getTexts();
      setTexts(textsData);
    } catch (error) {
      console.error('Failed to load texts:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const validateForm = () => {
    const errors = { title: '', grade: '', body: '' };
    let isValid = true;

    if (!formData.title.trim()) {
      errors.title = 'Başlık gereklidir';
      isValid = false;
    }

    if (!formData.grade) {
      errors.grade = 'Sınıf seviyesi gereklidir';
      isValid = false;
    }

    if (!formData.body.trim()) {
      errors.body = 'Metin içeriği gereklidir';
      isValid = false;
    }

    setFormErrors(errors);
    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      if (editingText) {
        // Update existing text
        await apiClient.updateText(editingText.id, {
          title: formData.title.trim(),
          grade: parseInt(formData.grade),
          body: formData.body.trim()
        });
      } else {
        // Create new text
        await apiClient.createText({
          title: formData.title.trim(),
          grade: parseInt(formData.grade),
          body: formData.body.trim()
        });
      }

      // Reload texts
      await loadTexts();
      
      // Reset form
      setFormData({ title: '', grade: '', body: '' });
      setFormErrors({ title: '', grade: '', body: '' });
      setShowAddModal(false);
      setEditingText(null);
      
    } catch (error) {
      console.error('Failed to save text:', error);
      alert('Metin kaydedilemedi. Lütfen tekrar deneyin.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (text: Text) => {
    setEditingText(text);
    setFormData({
      title: text.title,
      grade: text.grade.toString(),
      body: text.body
    });
    setShowAddModal(true);
  };

  const handleDelete = async (textId: string) => {
    if (!confirm('Bu metni silmek istediğinizden emin misiniz?')) {
      return;
    }

    try {
      await apiClient.deleteText(textId);
      await loadTexts();
    } catch (error) {
      console.error('Failed to delete text:', error);
      alert('Metin silinemedi. Lütfen tekrar deneyin.');
    }
  };

  const handleOpenModal = () => {
    setEditingText(null);
    setFormData({ title: '', grade: '', body: '' });
    setFormErrors({ title: '', grade: '', body: '' });
    setShowAddModal(true);
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    setEditingText(null);
    setFormData({ title: '', grade: '', body: '' });
    setFormErrors({ title: '', grade: '', body: '' });
  };

  // ESC key to close modal
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleCloseModal();
      }
    };

    if (showAddModal) {
      document.addEventListener('keydown', handleEsc);
      return () => document.removeEventListener('keydown', handleEsc);
    }
  }, [showAddModal]);

  // Show loading spinner while checking authentication
  if (isAuthLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // If not authenticated, show loading or redirect
  if (!isAuthenticated) {
    if (isAuthLoading) {
      console.log('🔍 TextsPage: Showing auth loading spinner');
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Kimlik doğrulanıyor...</p>
          </div>
        </div>
      );
    }
    
    console.log('🔍 TextsPage: Not authenticated, redirecting to login');
    return null; // Will redirect via useEffect
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className={combineThemeClasses('min-h-screen', themeColors.background.secondary)}>
      <Navigation />

      {/* Content */}
      <div className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
        <div className="space-y-4 sm:space-y-6">
          {/* Add Text Button */}
          {hasPermission('text:create') && (
            <div className="flex justify-end">
              <button
                onClick={handleOpenModal}
                className="w-full sm:w-auto px-4 sm:px-6 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors text-sm flex items-center justify-center"
              >
                <span className="text-lg mr-2">➕</span>
                Metin Ekle
              </button>
            </div>
          )}

          {/* Texts List */}
          {texts.length === 0 ? (
            <div className="bg-white dark:bg-slate-800 shadow rounded-lg p-6 sm:p-8 text-center border border-gray-200 dark:border-slate-700">
              <div className="text-gray-500 dark:text-slate-400 text-base sm:text-lg">
                Henüz metin bulunmuyor
              </div>
              <div className="text-gray-400 dark:text-slate-500 text-sm mt-2">
                Yeni metin eklemek için yukarıdaki butona tıklayın
              </div>
            </div>
          ) : (
            <div className="grid gap-3 sm:gap-4">
              {texts.map((text) => (
                <div key={text.id} className="bg-white dark:bg-slate-800 shadow rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-slate-700">
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between space-y-3 sm:space-y-0">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base sm:text-lg font-medium text-gray-900 dark:text-slate-100 truncate">
                        {text.title}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-slate-400 mt-1">
                        {text.grade === 0 ? 'Diğer' : `Sınıf ${text.grade}`} • {formatTurkishDate(text.created_at)}
                      </p>
                      <p className="text-gray-700 dark:text-slate-300 mt-3 line-clamp-3">
                        {text.body}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2 sm:ml-4">
                      {hasPermission('text:update') && (
                        <button
                          onClick={() => handleEdit(text)}
                          className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-md hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                        >
                          Düzenle
                        </button>
                      )}
                      {hasPermission('text:delete') && (
                        <button
                          onClick={() => handleDelete(text.id)}
                          className="px-3 py-1 text-sm bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-md hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
                        >
                          Sil
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-slate-600">
              <h2 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-slate-100">
                {editingText ? 'Metni Düzenle' : 'Yeni Metin Ekle'}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-slate-300 transition-colors"
              >
                <span className="text-2xl">×</span>
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4 sm:space-y-6">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                  Başlık <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100"
                  placeholder="Metin başlığını girin"
                />
                {formErrors.title && (
                  <div className="text-red-600 dark:text-red-400 text-sm mt-1">{formErrors.title}</div>
                )}
              </div>

              {/* Grade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                  Sınıf Seviyesi <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.grade}
                  onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                  className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100"
                >
                  <option value="">Sınıf seçin</option>
                  <option value="1">1. Sınıf</option>
                  <option value="2">2. Sınıf</option>
                  <option value="3">3. Sınıf</option>
                  <option value="4">4. Sınıf</option>
                  <option value="5">5. Sınıf</option>
                  <option value="6">6. Sınıf</option>
                  <option value="0">Diğer</option>
                </select>
                {formErrors.grade && (
                  <div className="text-red-600 dark:text-red-400 text-sm mt-1">{formErrors.grade}</div>
                )}
              </div>

              {/* Body */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                  Metin İçeriği <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.body}
                  onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                  rows={6}
                  className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100"
                  placeholder="Okuma analizi yapılacak metni buraya yazın..."
                />
                {formErrors.body && (
                  <div className="text-red-600 dark:text-red-400 text-sm mt-1">{formErrors.body}</div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-3 pt-4 border-t border-gray-200 dark:border-slate-600">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="w-full sm:w-auto px-6 py-2 text-sm font-medium text-gray-700 dark:text-slate-300 bg-gray-100 dark:bg-slate-700 rounded-md hover:bg-gray-200 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full sm:w-auto px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
                >
                  {isSubmitting ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Kaydediliyor...
                    </div>
                  ) : (
                    editingText ? 'Güncelle' : 'Kaydet'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}