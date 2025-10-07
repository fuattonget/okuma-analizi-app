'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient, Student, AnalysisSummary, Text } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { useRoles } from '@/lib/useRoles';
import { useAnalysisStore } from '@/lib/store';
import Navigation from '@/components/Navigation';
import Breadcrumbs from '@/components/Breadcrumbs';
import { formatTurkishDate } from '@/lib/dateUtils';
import { themeColors, combineThemeClasses, componentClasses } from '@/lib/theme';
import {
  UserIcon,
  AnalysisIcon,
  AudioIcon,
  BookIcon,
  SearchIcon,
  ViewIcon,
  CalendarIcon,
  ClockIcon,
  CheckIcon,
  CrossIcon,
  WarningIcon,
  GradeIcon,
  RefreshIcon,
  LightbulbIcon,
  MusicIcon,
  EditIcon,
  LockIcon
} from '@/components/Icon';

export default function StudentProfilePage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated, isAuthLoading } = useAuth();
  const { hasPermission } = useRoles();
  const { startPolling, stopPolling, stopAllPolling, updateAnalysis } = useAnalysisStore();
  
  const [student, setStudent] = useState<Student | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showNewAnalysisModal, setShowNewAnalysisModal] = useState(false);
  
  // Analysis popup states
  const [texts, setTexts] = useState<Text[]>([]);
  const [filteredTexts, setFilteredTexts] = useState<Text[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedTextId, setSelectedTextId] = useState<string>('');
  const [selectedGrade, setSelectedGrade] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  
  // Edit and status management
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState({
    first_name: '',
    last_name: '',
    grade: ''
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmAction, setConfirmAction] = useState<'deactivate' | 'activate' | null>(null);
  const [showEditConfirmDialog, setShowEditConfirmDialog] = useState(false);

  const loadStudentData = useCallback(async (studentId: string) => {
    try {
      setLoading(true);
      console.log('🔄 Loading student data for:', studentId);
      
      // Load student details
      const studentData = await apiClient.getStudent(studentId);
      setStudent(studentData);
      console.log('👤 Student loaded:', studentData);
      
      // Load student's analyses only if user has permission
      if (hasPermission('analysis:read') || hasPermission('analysis_management')) {
        try {
          const studentAnalyses = await apiClient.getAnalyses(50, studentId);
          setAnalyses(studentAnalyses);
          console.log('📊 Student analyses loaded:', studentAnalyses);
          
          // Start polling for running/queued analyses
          studentAnalyses.forEach(analysis => {
            if (analysis.status === 'running' || analysis.status === 'queued') {
              console.log('🔄 Starting polling for analysis:', analysis.id, 'status:', analysis.status);
              startPolling(analysis.id, async () => {
                try {
                  const updatedAnalysis = await apiClient.getAnalysis(analysis.id);
                  console.log('📊 Polling update for analysis:', analysis.id, 'new status:', updatedAnalysis.status);
                  
                  // Update local state
                  setAnalyses(prev => prev.map(a => 
                    a.id === analysis.id ? { ...a, status: updatedAnalysis.status } : a
                  ));
                  
                  if (updatedAnalysis.status === 'done' || updatedAnalysis.status === 'failed') {
                    console.log('✅ Analysis completed, stopping polling for:', analysis.id);
                    stopPolling(analysis.id);
                  }
                } catch (error) {
                  console.error(`❌ Failed to poll analysis ${analysis.id}:`, error);
                  stopPolling(analysis.id);
                }
              });
            }
          });
        } catch (err) {
          console.error('❌ Failed to load analyses:', err);
          // Don't fail the whole page if analyses can't be loaded
        }
      } else {
        console.log('ℹ️ User does not have permission to view analyses');
      }
      
    } catch (err) {
      console.error('❌ Error loading student data:', err);
      setError('Öğrenci verileri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  }, [startPolling, stopPolling, hasPermission]);

  useEffect(() => {
    if (isAuthenticated && params.id) {
      loadStudentData(params.id as string);
    }
    
    // Cleanup polling on unmount
    return () => {
      stopAllPolling();
    };
  }, [isAuthenticated, params.id, loadStudentData, stopAllPolling]);

  const loadTexts = useCallback(async () => {
    try {
      console.log('📚 Loading texts...');
      const textsData = await apiClient.getTexts();
      setTexts(textsData);
      console.log('📚 Texts loaded:', textsData);
    } catch (error) {
      console.error('❌ Failed to load texts:', error);
    }
  }, []);

  const autoSelectTextByGrade = useCallback((grade: number) => {
    if (!texts.length) return;
    
    // Find text matching the student's grade
    const matchingText = texts.find(text => text.grade === grade);
    if (matchingText) {
      setSelectedTextId(matchingText.id);
      console.log('📝 Auto-selected text for grade', grade, ':', matchingText.title);
    } else {
      // If no exact match, select first text of same grade level
      const gradeTexts = texts.filter(text => text.grade === grade);
      if (gradeTexts.length > 0) {
        setSelectedTextId(gradeTexts[0].id);
        console.log('📝 Auto-selected first text for grade', grade, ':', gradeTexts[0].title);
      }
    }
  }, [texts]);

  // Filter texts by selected grade
  useEffect(() => {
    if (selectedGrade && selectedGrade !== '') {
      const filtered = texts.filter(t => t.grade === parseInt(selectedGrade));
      setFilteredTexts(filtered);
    } else {
      setFilteredTexts(texts);
    }
  }, [texts, selectedGrade]);

  // Auto-select text when texts are loaded and modal is open
  useEffect(() => {
    if (showNewAnalysisModal && texts.length > 0 && student) {
      // Set grade to student's grade initially
      setSelectedGrade(student.grade.toString());
      autoSelectTextByGrade(student.grade);
    }
  }, [showNewAnalysisModal, texts, student, autoSelectTextByGrade]);

  const handleStartNewAnalysis = () => {
    // Open analysis modal instead of navigating
    handleOpenAnalysisModal();
  };

  const handleOpenAnalysisModal = async () => {
    setShowNewAnalysisModal(true);
    setUploadError(null);
    setUploadSuccess(false);
    setSelectedFile(null);
    setSelectedTextId('');
    setSelectedGrade('');
    
    // Load texts and auto-select based on student grade
    await loadTexts();
    if (student) {
      setSelectedGrade(student.grade.toString());
      autoSelectTextByGrade(student.grade);
    }
  };

  const handleCloseAnalysisModal = () => {
    setShowNewAnalysisModal(false);
    setSelectedFile(null);
    setSelectedTextId('');
    setSelectedGrade('');
    setUploadError(null);
    setUploadSuccess(false);
  };

  // Edit student functions
  const handleEditClick = () => {
    if (student) {
      setEditForm({
        first_name: student.first_name,
        last_name: student.last_name,
        grade: student.grade.toString()
      });
      setShowEditModal(true);
    }
  };

  const handleEditCancel = () => {
    setShowEditModal(false);
    setEditForm({
      first_name: '',
      last_name: '',
      grade: ''
    });
  };

  const handleEditSave = () => {
    setShowEditConfirmDialog(true);
  };

  const confirmEditSave = async () => {
    if (!student) return;
    
    try {
      setIsUpdating(true);
      const updatedStudent = await apiClient.updateStudent(student.id, {
        first_name: editForm.first_name,
        last_name: editForm.last_name,
        grade: parseInt(editForm.grade)
      });
      
      setStudent(updatedStudent);
      setShowEditModal(false);
      setShowEditConfirmDialog(false);
      console.log('✅ Student updated successfully');
    } catch (error) {
      console.error('❌ Failed to update student:', error);
      setError('Öğrenci güncellenirken hata oluştu');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleStatusChange = (action: 'deactivate' | 'activate') => {
    setConfirmAction(action);
    setShowConfirmDialog(true);
  };

  const confirmStatusChange = async () => {
    if (!student || !confirmAction) return;
    
    try {
      setIsUpdating(true);
      const updatedStudent = await apiClient.updateStudent(student.id, {
        is_active: confirmAction === 'activate'
      });
      
      setStudent(updatedStudent);
      setShowConfirmDialog(false);
      setConfirmAction(null);
      console.log(`✅ Student ${confirmAction}d successfully`);
    } catch (error) {
      console.error(`❌ Failed to ${confirmAction} student:`, error);
      setError(`Öğrenci ${confirmAction === 'activate' ? 'aktifleştirilirken' : 'pasifleştirilirken'} hata oluştu`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadError(null);
    }
  };

  const handleTextSelect = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedTextId(event.target.value);
  };

  const handleGradeSelect = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedGrade(event.target.value);
    setSelectedTextId(''); // Reset text selection when grade changes
  };

  const handleStartAnalysis = async () => {
    if (!selectedFile || !selectedTextId || !selectedGrade || !student) {
      setUploadError('Lütfen ses dosyası, sınıf ve metin seçin');
      return;
    }

    setIsUploading(true);
    setUploadError(null);

    try {
      console.log('🚀 Starting analysis for student:', student.id);
      const response = await apiClient.uploadAudio(selectedFile, selectedTextId, student.id);
      
      setUploadSuccess(true);
      console.log('✅ Analysis started successfully:', response.analysis_id);
      
      // Close modal after 2 seconds
      setTimeout(() => {
        handleCloseAnalysisModal();
        // Reload student data to show new analysis
        loadStudentData(student.id);
      }, 2000);
      
    } catch (error: any) {
      console.error('❌ Analysis failed:', error);
      setUploadError('Analiz başlatılamadı. Lütfen tekrar deneyin.');
    } finally {
      setIsUploading(false);
    }
  };

  const getGradeText = (grade: number) => {
    return grade === 0 ? 'Diğer' : `${grade}. Sınıf`;
  };

  const getStatusBadge = (isActive: boolean) => {
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        isActive 
          ? 'bg-green-100 text-green-800' 
          : 'bg-red-100 text-red-800'
      }`}>
        {isActive ? 'Aktif' : 'Pasif'}
      </span>
    );
  };

  const getAnalysisStatusBadge = (status: string) => {
    const statusClasses = {
      'done': 'bg-green-100 text-green-800',
      'running': 'bg-blue-100 text-blue-800',
      'queued': 'bg-yellow-100 text-yellow-800',
      'failed': 'bg-red-100 text-red-800'
    };
    
    const statusLabels = {
      'done': 'Tamamlandı',
      'running': 'Çalışıyor',
      'queued': 'Beklemede',
      'failed': 'Hata'
    };

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        statusClasses[status as keyof typeof statusClasses] || 'bg-gray-100 text-gray-800'
      }`}>
        {statusLabels[status as keyof typeof statusLabels] || status}
      </span>
    );
  };

  if (isAuthLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    router.push('/login');
    return null;
  }

  if (loading) {
    return (
      <div className={combineThemeClasses('min-h-screen', themeColors.background.secondary)}>
        <Navigation />
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-500">Yükleniyor...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !student) {
    return (
      <div className={combineThemeClasses('min-h-screen', themeColors.background.secondary)}>
        <Navigation />
        <div className="container mx-auto px-4 py-6">
          <div className="text-center py-8">
            <p className="text-red-600 mb-4">{error || 'Öğrenci bulunamadı'}</p>
            <button
              onClick={() => router.push('/students')}
              className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors dark:bg-indigo-600 dark:hover:bg-indigo-700 dark:focus:ring-indigo-400"
            >
              ← Öğrenci Listesine Dön
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={combineThemeClasses('min-h-screen', themeColors.background.secondary)}>
      <Navigation />
      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Breadcrumbs */}
        <Breadcrumbs />
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => router.push('/students')}
            className="px-4 py-2 bg-gray-200 text-gray-800 font-medium rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600 dark:focus:ring-slate-400"
          >
            ← Öğrenci Listesi
          </button>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleEditClick}
              disabled={isUpdating}
              className="px-4 py-2 bg-gray-600 text-white font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors dark:bg-gray-600 dark:hover:bg-gray-700 dark:focus:ring-gray-400 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              Düzenle
            </button>
            
            {student?.is_active ? (
              <button
                onClick={() => handleStatusChange('deactivate')}
                disabled={isUpdating}
                className="px-4 py-2 bg-red-600 text-white font-medium rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors dark:bg-red-600 dark:hover:bg-red-700 dark:focus:ring-red-400 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <LockIcon size="sm" className="inline mr-2" />
                Pasife Düşür
              </button>
            ) : (
              <button
                onClick={() => handleStatusChange('activate')}
                disabled={isUpdating}
                className="px-4 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors dark:bg-green-600 dark:hover:bg-green-700 dark:focus:ring-green-400 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Aktifleştir
              </button>
            )}
            
            {(hasPermission('analysis:create') || hasPermission('analysis_management')) && (
              <button
                onClick={handleOpenAnalysisModal}
                className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors dark:bg-indigo-600 dark:hover:bg-indigo-700 dark:focus:ring-indigo-400 flex items-center"
              >
                <AnalysisIcon size="sm" className="inline mr-2" />
                Yeni Analiz Yap
              </button>
            )}
          </div>
        </div>

        {/* Student Info Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-indigo-600">
                  {student.first_name.charAt(0)}{student.last_name.charAt(0)}
                </span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {student.first_name} {student.last_name}
                </h1>
                <div className="flex items-center space-x-4 mt-2">
                  <span className="text-sm text-gray-500">
                    <BookIcon size="sm" className="inline mr-1" />
                    Kayıt No: #{student.registration_number}
                  </span>
                  <span className="text-sm text-gray-500">
                    <GradeIcon size="sm" className="inline mr-1" />
                    {getGradeText(student.grade)}
                  </span>
                  {getStatusBadge(student.is_active)}
                </div>
                <div className="flex items-center space-x-4 mt-1">
                  <span className="text-sm text-gray-500">
                    <CalendarIcon size="sm" className="inline mr-1" />
                    Kayıt Tarihi: {formatTurkishDate(student.created_at)}
                  </span>
                  <span className="text-sm text-gray-500">
                    <UserIcon size="sm" className="inline mr-1" />
                    Kayıt Eden: {student.created_by}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Analysis History */}
        {(hasPermission('analysis:read') || hasPermission('analysis_management')) ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                <AnalysisIcon size="sm" className="inline mr-2" />
                Analiz Geçmişi ({analyses.length})
              </h2>
            </div>
            
            {analyses.length === 0 ? (
              <div className="p-6 text-center">
                <div className="mb-4">
                  <AnalysisIcon size="xl" className="text-gray-400" />
                </div>
                <p className="text-gray-500 mb-4">Bu öğrenci için henüz analiz yapılmamış</p>
                {(hasPermission('analysis:create') || hasPermission('analysis_management')) && (
                  <button
                    onClick={handleStartNewAnalysis}
                    className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors dark:bg-indigo-600 dark:hover:bg-indigo-700 dark:focus:ring-indigo-400"
                  >
                    🚀 İlk Analizi Başlat
                  </button>
                )}
              </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Metin
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Durum
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tarih
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Süre
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İşlem
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {analyses.map((analysis) => (
                    <tr key={analysis.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {analysis.text_title}
                        </div>
                        <div className="text-sm text-gray-500">
                          Metin Detayı
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getAnalysisStatusBadge(analysis.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatTurkishDate(analysis.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        -
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {analysis.status === 'done' ? (
                          <button
                            onClick={() => router.push(`/students/${params.id}/analysis/${analysis.id}`)}
                            className="text-indigo-600 hover:text-indigo-900"
                          >
                            <ViewIcon size="xs" className="inline mr-1" />
                            Görüntüle
                          </button>
                        ) : (
                          <span className="text-gray-400">Bekleniyor...</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          </div>
        ) : (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
            <div className="flex items-center">
              <LockIcon size="lg" className="text-yellow-600 dark:text-yellow-400 mr-4" />
              <div>
                <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200">
                  Yetki Gerekli
                </h3>
                <p className="text-yellow-700 dark:text-yellow-300 mt-1">
                  Analiz geçmişini görüntülemek için <strong className="font-semibold">"Analiz Listele"</strong> yetkisine ihtiyacınız var.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Analysis Modal */}
      {showNewAnalysisModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* Modal Header */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">
                  <AudioIcon size="sm" className="inline mr-2" />
                  Yeni Analiz - {student?.first_name} {student?.last_name}
                </h3>
                <button
                  onClick={handleCloseAnalysisModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Success Message */}
              {uploadSuccess && (
                <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
                  <CheckIcon size="sm" className="inline mr-2" />
                  Analiz başlatıldı! Yönlendiriliyorsunuz...
                </div>
              )}

              {/* Error Message */}
              {uploadError && (
                <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                  <CrossIcon size="sm" className="inline mr-2" />
                  {uploadError}
                </div>
              )}

              {/* Modal Content */}
              <div className="space-y-6">
                {/* File Upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                    <AudioIcon size="sm" className="inline mr-1" />
                    Ses Dosyası *
                  </label>
                  <div 
                    className="border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-lg p-6 text-center hover:border-gray-400 dark:hover:border-slate-500 transition-colors cursor-pointer bg-white dark:bg-slate-800"
                    onClick={() => document.getElementById('audio-upload')?.click()}
                  >
                    <input
                      type="file"
                      accept="audio/*"
                      onChange={handleFileSelect}
                      className="hidden"
                      id="audio-upload"
                      disabled={isUploading}
                    />
                    <div className="cursor-pointer">
                      {selectedFile ? (
                        <div className="text-green-600">
                          <div className="mb-2">
                            <AudioIcon size="lg" className="text-gray-400" />
                          </div>
                          <div className="font-medium">{selectedFile.name}</div>
                          <div className="text-sm text-gray-500">
                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                          </div>
                        </div>
                      ) : (
                        <div className="text-gray-500 dark:text-slate-400">
                          <div className="mb-2">
                            <AudioIcon size="lg" className="text-gray-400 dark:text-slate-500" />
                          </div>
                          <div className="font-medium">Ses dosyasını seçin</div>
                          <div className="text-sm">MP3, WAV, M4A, AAC, OGG, FLAC</div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Grade Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                    <GradeIcon size="sm" className="inline mr-1" />
                    Sınıf Seviyesi *
                  </label>
                  <select
                    value={selectedGrade}
                    onChange={handleGradeSelect}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100"
                    disabled={isUploading}
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
                </div>

                {/* Text Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                    <BookIcon size="sm" className="inline mr-1" />
                    Metin Seçimi *
                  </label>
                  <select
                    value={selectedTextId}
                    onChange={handleTextSelect}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100"
                    disabled={isUploading || !selectedGrade}
                  >
                    <option value="">{selectedGrade ? 'Metin seçin' : 'Önce sınıf seçin'}</option>
                    {filteredTexts.map((text) => (
                      <option key={text.id} value={text.id}>
                        {text.title} ({text.grade === 0 ? 'Diğer' : `${text.grade}. Sınıf`})
                      </option>
                    ))}
                  </select>
                  {selectedTextId && (
                    <div className="mt-2 p-3 bg-gray-50 dark:bg-slate-700 rounded-md">
                      <div className="text-sm font-medium text-gray-900 dark:text-slate-100">
                        <BookIcon size="sm" className="inline mr-1" />
                        Seçilen Metin
                      </div>
                      <div className="text-sm text-gray-600 dark:text-slate-300 mt-1">
                        {filteredTexts.find(t => t.id === selectedTextId)?.body?.substring(0, 200)}
                        {filteredTexts.find(t => t.id === selectedTextId)?.body && filteredTexts.find(t => t.id === selectedTextId)?.body!.length > 200 && '...'}
                      </div>
                    </div>
                  )}
                </div>

                {/* Student Info */}
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-semibold">
                        {student?.first_name?.charAt(0)}{student?.last_name?.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <div className="font-medium text-blue-900">
                        {student?.first_name} {student?.last_name}
                      </div>
                      <div className="text-sm text-blue-600">
                        {getGradeText(student?.grade || 0)}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-200">
                <button
                  onClick={handleCloseAnalysisModal}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                  disabled={isUploading}
                >
                  İptal
                </button>
                <button
                  onClick={handleStartAnalysis}
                  disabled={!selectedFile || !selectedTextId || !selectedGrade || isUploading}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Analiz Ediliyor...
                    </div>
                  ) : (
                    'Analiz Et'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              <EditIcon size="sm" className="inline mr-2" />
              Öğrenci Düzenle
            </h2>
              <button
                onClick={handleEditCancel}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <span className="text-2xl">×</span>
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={(e) => { e.preventDefault(); handleEditSave(); }} className="p-6 space-y-4">
              {/* First Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <UserIcon size="sm" className="inline mr-1" />
                  Ad <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={editForm.first_name}
                  onChange={(e) => setEditForm(prev => ({ ...prev, first_name: e.target.value }))}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Öğrencinin adını girin"
                  maxLength={50}
                  required
                />
              </div>

              {/* Last Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <UserIcon size="sm" className="inline mr-1" />
                  Soyad <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={editForm.last_name}
                  onChange={(e) => setEditForm(prev => ({ ...prev, last_name: e.target.value }))}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="Öğrencinin soyadını girin"
                  maxLength={50}
                  required
                />
              </div>

              {/* Grade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <GradeIcon size="sm" className="inline mr-1" />
                  Sınıf <span className="text-red-500">*</span>
                </label>
                <select
                  value={editForm.grade}
                  onChange={(e) => setEditForm(prev => ({ ...prev, grade: e.target.value }))}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  required
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
              </div>

            </form>

            {/* Modal Footer */}
            <div className="flex justify-end space-x-3 p-6 border-t border-gray-200">
              <button
                onClick={handleEditCancel}
                disabled={isUpdating}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                İptal
              </button>
              <button
                onClick={handleEditSave}
                disabled={isUpdating || !editForm.first_name || !editForm.last_name || !editForm.grade}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUpdating ? 'Kaydediliyor...' : 'Kaydet'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Confirmation Dialog */}
      {showEditConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-4">
              Öğrenci Bilgilerini Güncelle
            </h3>
            <p className="text-gray-600 dark:text-slate-300 mb-6">
              Öğrenci bilgilerini güncellemek istediğinizden emin misiniz? Bu işlem geri alınamaz.
            </p>
            <div className="flex items-center space-x-3">
              <button
                onClick={confirmEditSave}
                disabled={isUpdating}
                className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUpdating ? 'Güncelleniyor...' : 'Evet, Güncelle'}
              </button>
              <button
                onClick={() => setShowEditConfirmDialog(false)}
                disabled={isUpdating}
                className="px-4 py-2 bg-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                İptal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-4">
              {confirmAction === 'deactivate' ? 'Öğrenciyi Pasifleştir' : 'Öğrenciyi Aktifleştir'}
            </h3>
            <p className="text-gray-600 dark:text-slate-300 mb-6">
              {confirmAction === 'deactivate' 
                ? 'Bu öğrenciyi pasifleştirmek istediğinizden emin misiniz? Pasif öğrenciler analiz yapamaz.'
                : 'Bu öğrenciyi aktifleştirmek istediğinizden emin misiniz?'
              }
            </p>
            <div className="flex items-center space-x-3">
              <button
                onClick={confirmStatusChange}
                disabled={isUpdating}
                className={`px-4 py-2 text-white font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                  confirmAction === 'deactivate' 
                    ? 'bg-red-600 hover:bg-red-700 focus:ring-red-500' 
                    : 'bg-green-600 hover:bg-green-700 focus:ring-green-500'
                }`}
              >
                {isUpdating ? 'İşleniyor...' : (confirmAction === 'deactivate' ? 'Pasifleştir' : 'Aktifleştir')}
              </button>
              <button
                onClick={() => {
                  setShowConfirmDialog(false);
                  setConfirmAction(null);
                }}
                disabled={isUpdating}
                className="px-4 py-2 bg-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                İptal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
