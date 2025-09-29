'use client';

import { useState, useEffect, useCallback } from 'react';
import { apiClient, Text } from '@/lib/api';
import { formatTurkishDateOnly } from '@/lib/dateUtils';
import classNames from 'classnames';

export default function TextsPage() {
  const [texts, setTexts] = useState<Text[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingText, setEditingText] = useState<Text | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [deletingText, setDeletingText] = useState<Text | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    grade: '',
    body: '',
    comment: ''
  });
  const [formErrors, setFormErrors] = useState({
    title: '',
    grade: '',
    body: '',
    comment: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

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

  useEffect(() => {
    loadTexts();
  }, []);

  const handleCreate = () => {
    setEditingText(null);
    setFormData({ title: '', grade: '', body: '', comment: '' });
    setFormErrors({ title: '', grade: '', body: '', comment: '' });
    setShowForm(true);
  };

  const handleEdit = (text: Text) => {
    setEditingText(text);
    setFormData({
      title: text.title,
      grade: text.grade.toString(),
      body: text.body,
      comment: text.comment || ''
    });
    setFormErrors({ title: '', grade: '', body: '', comment: '' });
    setShowForm(true);
  };

  const handleDeleteClick = (text: Text) => {
    setDeletingText(text);
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!deletingText) return;
    
    try {
      await apiClient.deleteText(deletingText.id);
      setTexts(texts.filter(t => t.id !== deletingText.id));
      setShowDeleteModal(false);
      setDeletingText(null);
    } catch (error) {
      console.error('Failed to delete text:', error);
      alert('Metin silinirken hata oluştu');
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
    setDeletingText(null);
  };

  // Form validation
  const validateForm = () => {
    const errors = { title: '', grade: '', body: '', comment: '' };
    let isValid = true;

    // Title validation
    if (!formData.title.trim()) {
      errors.title = 'Metin başlığı gereklidir';
      isValid = false;
    } else if (formData.title.trim().length < 3) {
      errors.title = 'Metin başlığı en az 3 karakter olmalıdır';
      isValid = false;
    } else if (formData.title.trim().length > 200) {
      errors.title = 'Metin başlığı en fazla 200 karakter olabilir';
      isValid = false;
    }

    // Grade validation
    if (!formData.grade) {
      errors.grade = 'Sınıf seviyesi seçilmelidir';
      isValid = false;
    } else if (!['1', '2', '3', '4'].includes(formData.grade)) {
      errors.grade = 'Geçersiz sınıf seviyesi';
      isValid = false;
    }

    // Body validation
    if (!formData.body.trim()) {
      errors.body = 'Metin içeriği gereklidir';
      isValid = false;
    } else if (formData.body.trim().length < 10) {
      errors.body = 'Metin içeriği en az 10 karakter olmalıdır';
      isValid = false;
    } else if (formData.body.trim().length > 10000) {
      errors.body = 'Metin içeriği en fazla 10,000 karakter olabilir';
      isValid = false;
    }

    // Comment validation (optional)
    if (formData.comment && formData.comment.length > 500) {
      errors.comment = 'Yorum en fazla 500 karakter olabilir';
      isValid = false;
    }

    setFormErrors(errors);
    return isValid;
  };

  // Sanitize input
  const sanitizeInput = (input: string) => {
    return input
      .trim()
      .replace(/[<>]/g, '') // Remove potential HTML tags
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .replace(/on\w+=/gi, '') // Remove event handlers
      .replace(/'/g, "'") // Normalize curly quotes to ASCII apostrophe
      .replace(/'/g, "'"); // Normalize curly quotes to ASCII apostrophe
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      // Debug: Log original form data
      console.log('Original form data:', formData);
      
      // Sanitize inputs
      const sanitizedData = {
        title: sanitizeInput(formData.title),
        grade: parseInt(formData.grade),
        body: sanitizeInput(formData.body),
        comment: formData.comment ? sanitizeInput(formData.comment) : ''
      };
      
      // Debug: Log sanitized data
      console.log('Sanitized data:', sanitizedData);

      if (editingText) {
        // Update existing text
        const updatedText = await apiClient.updateText(editingText.id, sanitizedData);
        setTexts(texts.map(t => t.id === editingText.id ? updatedText : t));
      } else {
        // Create new text
        const newText = await apiClient.createText(sanitizedData);
        setTexts([newText, ...texts]);
      }
      
      setShowForm(false);
      setFormData({ title: '', grade: '', body: '', comment: '' });
      setFormErrors({ title: '', grade: '', body: '', comment: '' });
    } catch (error: any) {
      console.error('Failed to save text:', error);
      
      // Better error handling
      let errorMessage = 'Metin kaydedilirken hata oluştu';
      if (error.response?.status === 400) {
        errorMessage = 'Girilen veriler geçersiz. Lütfen kontrol edin.';
      } else if (error.response?.status === 409) {
        errorMessage = 'Bu başlıkta bir metin zaten mevcut.';
      } else if (error.response?.status >= 500) {
        errorMessage = 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.';
      } else if (!navigator.onLine) {
        errorMessage = 'İnternet bağlantınızı kontrol edin.';
      }
      
      alert(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };


  const handleCancel = () => {
    setShowForm(false);
    setEditingText(null);
    setFormData({ title: '', grade: '', body: '', comment: '' });
    setFormErrors({ title: '', grade: '', body: '', comment: '' });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Yükleniyor...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Metin Yönetimi</h1>
        <button
          onClick={handleCreate}
          className="btn btn-primary"
        >
          Yeni Metin Ekle
        </button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">
              {editingText ? 'Metni Düzenle' : 'Yeni Metin Ekle'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Metin Başlığı <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className={`input w-full ${formErrors.title ? 'border-red-500' : ''}`}
                  placeholder="Metin başlığı"
                  maxLength={200}
                  required
                />
                <div className="flex justify-between items-center mt-1">
                  {formErrors.title && (
                    <span className="text-red-500 text-sm">{formErrors.title}</span>
                  )}
                  <span className="text-gray-400 text-sm ml-auto">
                    {formData.title.length}/200
                  </span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sınıf Seviyesi <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.grade}
                  onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                  className={`select w-full ${formErrors.grade ? 'border-red-500' : ''}`}
                  required
                >
                  <option value="">Seçiniz</option>
                  <option value="1">1. Sınıf</option>
                  <option value="2">2. Sınıf</option>
                  <option value="3">3. Sınıf</option>
                  <option value="4">4. Sınıf</option>
                </select>
                {formErrors.grade && (
                  <span className="text-red-500 text-sm mt-1">{formErrors.grade}</span>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Metin İçeriği <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.body}
                  onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                  className={`textarea w-full h-32 ${formErrors.body ? 'border-red-500' : ''}`}
                  placeholder="Metin içeriğini buraya yazın..."
                  maxLength={10000}
                  required
                />
                <div className="flex justify-between items-center mt-1">
                  {formErrors.body && (
                    <span className="text-red-500 text-sm">{formErrors.body}</span>
                  )}
                  <span className="text-gray-400 text-sm ml-auto">
                    {formData.body.length}/10,000
                  </span>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Yorum (Opsiyonel)
                </label>
                <textarea
                  value={formData.comment}
                  onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
                  className={`textarea w-full h-20 ${formErrors.comment ? 'border-red-500' : ''}`}
                  placeholder="Metin hakkında yorumunuz..."
                  maxLength={500}
                />
                <div className="flex justify-between items-center mt-1">
                  {formErrors.comment && (
                    <span className="text-red-500 text-sm">{formErrors.comment}</span>
                  )}
                  <span className="text-gray-400 text-sm ml-auto">
                    {formData.comment.length}/500
                  </span>
                </div>
              </div>
              
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={handleCancel}
                  className="btn btn-secondary"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {editingText ? 'Güncelleniyor...' : 'Kaydediliyor...'}
                    </>
                  ) : (
                    editingText ? 'Güncelle' : 'Kaydet'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}


      {/* Delete Confirmation Modal */}
      {showDeleteModal && deletingText && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 animate-fadeIn">
          <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-lg mx-4 transform transition-all duration-300 scale-100">
            {/* Header with Icon */}
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center animate-pulse">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </div>
            </div>
            
            {/* Content */}
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold text-gray-900 mb-3">
                Metni Sil
              </h3>
              <p className="text-gray-600 mb-6">
                <span className="font-semibold text-gray-900">"{deletingText.title}"</span> metnini silmek istediğinizden emin misiniz?
              </p>
              
              {/* Text Preview Card */}
              <div className="bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200 p-4 rounded-lg mb-6">
                <div className="flex items-center mb-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {deletingText.grade}. Sınıf
                  </span>
                  <span className="ml-2 text-xs text-gray-500">
                    {formatTurkishDateOnly(deletingText.created_at)}
                  </span>
                </div>
                <p className="text-sm text-gray-700 line-clamp-3 text-left">
                  {deletingText.body}
                </p>
                {deletingText.comment && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500 italic">
                      "{deletingText.comment}"
                    </p>
                  </div>
                )}
              </div>
              
              {/* Warning */}
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-red-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                  </svg>
                  <p className="text-sm text-red-800 font-medium">
                    Bu işlem geri alınamaz!
                  </p>
                </div>
                <p className="text-xs text-red-600 mt-1">
                  Metin veritabanından tamamen kaldırılacaktır.
                </p>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex gap-4 justify-center">
              <button
                onClick={handleDeleteCancel}
                className="px-6 py-3 text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 rounded-lg transition-all duration-200 hover:shadow-md"
              >
                <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
                İptal
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-6 py-3 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-all duration-200 hover:shadow-lg transform hover:scale-105"
              >
                <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
                Evet, Sil
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Texts List */}
      <div className="card">
        {texts.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">Henüz metin bulunmuyor</p>
            <button
              onClick={handleCreate}
              className="btn btn-primary"
            >
              İlk Metni Ekle
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {texts.map((text) => (
              <div
                key={text.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-medium text-gray-900">{text.title}</h3>
                    <span className="text-sm text-blue-600">
                      {text.grade}. Sınıf
                    </span>
                    {text.comment && (
                      <p className="text-sm text-gray-600 mt-1 italic">
                        "{text.comment}"
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(text)}
                      className="btn btn-sm btn-secondary"
                    >
                      Düzenle
                    </button>
                    <button
                      onClick={() => handleDeleteClick(text)}
                      className="btn btn-sm btn-danger"
                    >
                      Sil
                    </button>
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded">
                  {text.body}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
