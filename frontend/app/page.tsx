'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, Text, AnalysisSummary, Student } from '@/lib/api';
import { useAnalysisStore } from '@/lib/store';
import { useAuth } from '@/lib/useAuth';
import { useRoles } from '@/lib/useRoles';
import classNames from 'classnames';
import Navigation from '@/components/Navigation';
import Loading, { SkeletonCard, SkeletonList } from '@/components/Loading';
import Error, { ErrorToast, SuccessToast } from '@/components/Error';
import { AudioIcon, UserIcon, GradeIcon, BookIcon, AnalysisIcon } from '@/components/Icon';
import { themeColors, combineThemeClasses } from '@/lib/theme';

export default function HomePage() {
  const router = useRouter();
  const { analyses, setAnalyses, addAnalysis, updateAnalysis, startPolling, stopPolling, stopAllPolling } = useAnalysisStore();
  const { isAuthenticated, isAuthLoading } = useAuth();
  const { hasPermission } = useRoles();
  
  const [texts, setTexts] = useState<Text[]>([]);
  const [filteredTexts, setFilteredTexts] = useState<Text[]>([]);
  const [selectedTextId, setSelectedTextId] = useState<string>('');
  const [customText, setCustomText] = useState('');
  const [grade, setGrade] = useState<string>('');
  
  // Student selection
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudentId, setSelectedStudentId] = useState<string>('');
  
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [loadingTexts, setLoadingTexts] = useState(false);
  const [loadingStudents, setLoadingStudents] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showErrorToast, setShowErrorToast] = useState(false);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [formErrors, setFormErrors] = useState({
    file: '',
    text: '',
    grade: ''
  });


  // Handle token expiration and redirect
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      console.log('🔍 HomePage: User not authenticated, redirecting to login');
      router.push('/login');
    }
  }, [isAuthenticated, isAuthLoading, router]);

  // Load data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      loadTexts();
      loadAnalyses();
      loadStudents();
    }
    
    // Cleanup polling on unmount
    return () => {
      stopAllPolling();
    };
  }, [isAuthenticated]);


  // Filter texts by grade
  useEffect(() => {
    console.log('🔍 Filtering texts:', { grade, textsCount: texts.length });
    if (grade && grade !== '') {
      const filtered = texts.filter(t => t.grade === parseInt(grade));
      console.log('📋 Filtered texts:', filtered);
      setFilteredTexts(filtered);
    } else {
      console.log('📋 All texts:', texts);
      setFilteredTexts(texts);
    }
  }, [texts, grade]);

  const loadTexts = useCallback(async () => {
    try {
      setLoadingTexts(true);
      setError(null);
      console.log('🔄 Loading texts...');
      const textsData = await apiClient.getTexts();
      console.log('📚 Texts loaded:', textsData);
      setTexts(textsData);
    } catch (error: any) {
      console.error('❌ Failed to load texts:', error);
      const errorMessage = error.response?.data?.detail || 'Metinler yüklenirken bir hata oluştu';
      setError(errorMessage);
      setShowErrorToast(true);
    } finally {
      setLoadingTexts(false);
    }
  }, []);

  const loadStudents = useCallback(async () => {
    try {
      setLoadingStudents(true);
      setError(null);
      console.log('🔄 Loading students...');
      const response = await apiClient.getStudents();
      console.log('👥 Students response:', response);
      const studentsData = Array.isArray(response) ? response : response.students || [];
      console.log('👥 Students data:', studentsData);
      console.log('👥 Students count:', studentsData?.length || 0);
      setStudents(studentsData);
    } catch (error: any) {
      console.error('❌ Failed to load students:', error);
      const errorMessage = error.response?.data?.detail || 'Öğrenciler yüklenirken bir hata oluştu';
      setError(errorMessage);
      setShowErrorToast(true);
      setStudents([]);
    } finally {
      setLoadingStudents(false);
    }
  }, []);

  const loadAnalyses = useCallback(async () => {
    try {
      const analysesData = await apiClient.getAnalyses(50);
      setAnalyses(analysesData);
      
      // Start polling for running/queued analyses
      analysesData.forEach(analysis => {
        if (analysis.status === 'running' || analysis.status === 'queued') {
          startPolling(analysis.id, async () => {
            try {
              const updatedAnalysis = await apiClient.getAnalysis(analysis.id);
              updateAnalysis(analysis.id, { status: updatedAnalysis.status });
              
              if (updatedAnalysis.status === 'done' || updatedAnalysis.status === 'failed') {
                updateAnalysis(analysis.id, updatedAnalysis);
                stopPolling(analysis.id);
              }
            } catch (error) {
              console.error(`Failed to poll analysis ${analysis.id}:`, error);
              stopPolling(analysis.id);
            }
          });
        }
      });
    } catch (error) {
      console.error('Failed to load analyses:', error);
    }
  }, [setAnalyses, startPolling, updateAnalysis, stopPolling]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  // File validation
  const validateAndSetFile = (file: File) => {
    const errors = { ...formErrors };
    
    // File size check (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      errors.file = 'Dosya boyutu 50MB\'dan büyük olamaz';
      setFormErrors(errors);
      return;
    }
    
    // File type check
    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/m4a', 'audio/x-m4a'];
    if (!allowedTypes.includes(file.type)) {
      errors.file = 'Desteklenmeyen dosya türü. MP3, WAV, M4A dosyaları kabul edilir.';
      setFormErrors(errors);
      return;
    }
    
    // Clear file error and set file
    errors.file = '';
    setFormErrors(errors);
    setSelectedFile(file);
  };

  const validateForm = () => {
    const errors = { ...formErrors };
    let isValid = true;
    
    // File validation
    if (!selectedFile) {
      errors.file = 'Lütfen bir ses dosyası seçin';
      isValid = false;
    }
    
    // Text validation
    if (!selectedTextId && !customText.trim()) {
      errors.text = 'Lütfen bir metin seçin veya özel metin girin';
      isValid = false;
    }
    
    // Grade validation
    if (!grade) {
      errors.grade = 'Lütfen sınıf seviyesi seçin';
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
      .replace(/"/g, '"') // Normalize curly quotes to ASCII quote
      .replace(/"/g, '"') // Normalize curly quotes to ASCII quote
      .replace(/'/g, "'") // Normalize curly quotes to ASCII apostrophe
      .replace(/…/g, '...') // Normalize ellipsis
      .replace(/–/g, '-') // Normalize en dash to hyphen
      .replace(/—/g, '-') // Normalize em dash to hyphen
      .replace(/[\u2018\u2019]/g, "'") // Normalize smart quotes
      .replace(/[\u201C\u201D]/g, '"') // Normalize smart quotes
      .replace(/[\u2026]/g, '...') // Normalize ellipsis
      .replace(/[\u2013\u2014]/g, '-') // Normalize dashes
      .replace(/[\u00A0]/g, ' ') // Normalize non-breaking space
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim();
  };

  const startAnalysis = async () => {
    // Validate form before proceeding
    if (!validateForm()) {
      return;
    }
    
    setIsUploading(true);
    try {
      // Sanitize custom text
      const sanitizedText = sanitizeInput(customText);
      
      // Create a temporary text if using custom text
      let textId = selectedTextId;
      if (!selectedTextId && sanitizedText.trim()) {
        const tempText = await apiClient.createText({
          title: `Geçici Metin - ${new Date().toLocaleString('tr-TR')}`,
          grade: parseInt(grade),
          body: sanitizedText.trim(),
        });
        textId = tempText.id;
        setTexts([tempText, ...texts]);
      } else if (selectedTextId) {
        const selectedText = texts.find(t => t.id === selectedTextId);
        if (selectedText) {
          textId = selectedText.id;
        }
      }
      
      console.log('🚀 Starting analysis with:', {
        textId,
        selectedStudentId,
        hasStudentId: !!selectedStudentId
      });
      const response = await apiClient.uploadAudio(selectedFile, textId, selectedStudentId || undefined);
      
      // Add to analyses list immediately
      const newAnalysis = {
        id: response.analysis_id,
        created_at: new Date().toISOString(),
        status: 'queued',
        text_title: texts.find(t => t.id === selectedTextId)?.title || 'Unknown',
        audio_id: '',
      };
      addAnalysis(newAnalysis);
      
      // Start polling for status updates
      startPolling(response.analysis_id, async () => {
        try {
          const analysis = await apiClient.getAnalysis(response.analysis_id);
          updateAnalysis(response.analysis_id, { status: analysis.status });
          
          if (analysis.status === 'done' || analysis.status === 'failed') {
            updateAnalysis(response.analysis_id, analysis);
            stopPolling(response.analysis_id);
          }
        } catch (error) {
          console.error(`Failed to poll analysis ${response.analysis_id}:`, error);
          stopPolling(response.analysis_id);
        }
      });
      
      // Show success message
      setShowSuccessToast(true);
      setTimeout(() => setShowSuccessToast(false), 5000);
      
      // Reset form
      setSelectedFile(null);
      setSelectedTextId('');
      setCustomText('');
      setGrade('');
      setFormErrors({ file: '', text: '', grade: '' });
      
    } catch (error: any) {
      console.error('Analysis failed:', error);
      let errorMessage = 'Analiz başlatılamadı. Lütfen tekrar deneyin.';
      
      if (error.response?.status === 401) {
        errorMessage = 'Oturum süreniz dolmuş. Lütfen tekrar giriş yapın.';
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        router.push('/login');
      } else if (error.response?.status === 413) {
        errorMessage = 'Dosya boyutu çok büyük. Lütfen daha küçük bir dosya seçin.';
      } else if (error.response?.status >= 500) {
        errorMessage = 'Sunucu hatası. Lütfen daha sonra tekrar deneyin.';
      } else if (!navigator.onLine) {
        errorMessage = 'İnternet bağlantınızı kontrol edin.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }
      
      setError(errorMessage);
      setShowErrorToast(true);
    } finally {
      setIsUploading(false);
    }
  };


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
      console.log('🔍 HomePage: Showing auth loading spinner');
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Kimlik doğrulanıyor...</p>
          </div>
        </div>
      );
    }
    
    console.log('🔍 HomePage: Not authenticated, redirecting to login');
    return null; // Will redirect via useEffect
  }

  return (
    <div className={combineThemeClasses('min-h-screen', themeColors.background.secondary)}>
      <Navigation />

      {/* Content */}
      <div className="max-w-7xl mx-auto py-4 sm:py-6 px-4 sm:px-6 lg:px-8">
        <div className="space-y-6 sm:space-y-8">
          {/* Upload Section */}
          <div className="bg-white dark:bg-slate-800 shadow rounded-lg border border-gray-200 dark:border-slate-700">
            <div className="px-4 sm:px-6 py-6 sm:py-8">
              <div className="text-center mb-6 sm:mb-8">
                <h2 className="text-xl sm:text-2xl font-semibold text-gray-900 dark:text-slate-100 flex items-center justify-center">
                  <span className="text-xl sm:text-2xl mr-2">🎤</span>
                  Ses Dosyası Analizi
                </h2>
              </div>
        
              <div className="space-y-6 sm:space-y-8">
                {/* File Upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-3 sm:mb-4">
                    <AudioIcon size="sm" className="mr-2" />
                    Ses Dosyası <span className="text-red-500">*</span>
                  </label>
                  <div
                    className={classNames(
                      'border-2 border-dashed rounded-lg p-4 sm:p-6 lg:p-8 text-center cursor-pointer transition-colors',
                      dragActive ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-slate-600',
                      selectedFile ? 'border-green-400 bg-green-50 dark:bg-green-900/20' : '',
                      formErrors.file ? 'border-red-400 bg-red-50 dark:bg-red-900/20' : ''
                    )}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                    onClick={() => document.getElementById('file-upload')?.click()}
                  >
                    <input
                      id="file-upload"
                      type="file"
                      accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg,.flac"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <div className="space-y-2">
                      <AudioIcon size="xl" />
                      <div className="text-base sm:text-lg font-medium text-gray-900 dark:text-slate-100">
                        {selectedFile ? selectedFile.name : 'Ses dosyasını buraya sürükleyin veya tıklayın'}
                      </div>
                      <div className="text-xs sm:text-sm text-gray-500 dark:text-slate-400">
                        MP3, WAV, M4A, AAC, OGG, FLAC formatları desteklenir
                      </div>
                      <div className="text-xs text-blue-600 dark:text-blue-400 mt-2">🤙</div>
                      {formErrors.file && (
                        <Error 
                          message={formErrors.file} 
                          type="warning" 
                          size="sm" 
                          showIcon={true}
                        />
                      )}
                    </div>
                  </div>
                </div>

                {/* Text Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-3 sm:mb-4">
                    Metin Seçimi <span className="text-red-500">*</span>
                  </label>
                  <div className="space-y-4 sm:space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                        <UserIcon size="sm" className="mr-2" />
                        Öğrenci Seçimi (İsteğe Bağlı)
                      </label>
                      {loadingStudents ? (
                        <div className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm bg-gray-50 dark:bg-slate-700">
                          <Loading variant="dots" size="sm" text="Öğrenciler yükleniyor..." />
                        </div>
                      ) : (
                        <select
                          value={selectedStudentId}
                          onChange={(e) => {
                            console.log('👥 Student selected:', e.target.value);
                            setSelectedStudentId(e.target.value);
                          }}
                          className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white dark:bg-slate-800 text-gray-900 dark:text-slate-100"
                        >
                          <option value="">Öğrenci seçin (isteğe bağlı)</option>
                          {students && students.length > 0 ? students
                            .filter(student => student.is_active)
                            .map((student) => (
                              <option key={student.id} value={student.id}>
                                {student.first_name} {student.last_name} - {student.grade === 0 ? 'Diğer' : `${student.grade}. Sınıf`}
                              </option>
                            )) : null}
                        </select>
                      )}
                    </div>

                    {/* Selected Student Preview */}
                    {selectedStudentId && students && students.length > 0 && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                          👤 Seçilen Öğrenci
                        </label>
                        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3">
                          <div className="flex items-center space-x-3">
                            <div className="w-8 h-8 bg-blue-100 dark:bg-blue-800 rounded-full flex items-center justify-center flex-shrink-0">
                              <span className="text-sm font-bold text-blue-600 dark:text-blue-300">
                                {students.find(s => s.id === selectedStudentId)?.first_name.charAt(0)}
                                {students.find(s => s.id === selectedStudentId)?.last_name.charAt(0)}
                              </span>
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-sm font-medium text-blue-900 dark:text-blue-100 truncate">
                                {students.find(s => s.id === selectedStudentId)?.first_name} {students.find(s => s.id === selectedStudentId)?.last_name}
                              </p>
                              <p className="text-xs text-blue-600 dark:text-blue-400">
                                {students.find(s => s.id === selectedStudentId)?.grade === 0 ? 'Diğer' : `${students.find(s => s.id === selectedStudentId)?.grade}. Sınıf`}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                        <GradeIcon size="sm" className="mr-2" />
                        Sınıf Seviyesi
                      </label>
                      <select
                        value={grade}
                        onChange={(e) => setGrade(e.target.value)}
                        className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white dark:bg-slate-800 text-gray-900 dark:text-slate-100"
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
                        <Error 
                          message={formErrors.grade} 
                          type="warning" 
                          size="sm" 
                          showIcon={true}
                        />
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                        <BookIcon size="sm" className="mr-2" />
                        Hazır Metinler
                      </label>
                      {loadingTexts ? (
                        <div className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm bg-gray-50 dark:bg-slate-700">
                          <Loading variant="dots" size="sm" text="Metinler yükleniyor..." />
                        </div>
                      ) : (
                        <select
                          value={selectedTextId}
                          onChange={(e) => {
                            console.log('📝 Text selected:', e.target.value);
                            setSelectedTextId(e.target.value);
                            setCustomText('');
                          }}
                          className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white dark:bg-slate-800 text-gray-900 dark:text-slate-100"
                        >
                          <option value="">Metin seçin</option>
                          {filteredTexts.map((text) => (
                            <option key={text.id} value={text.id}>
                              {text.title} (Sınıf {text.grade})
                            </option>
                          ))}
                        </select>
                      )}
                    </div>

                    {/* Selected Text Preview */}
                    {selectedTextId && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                          <BookIcon size="sm" className="mr-2" />
                          Seçilen Metin
                        </label>
                        <div className="bg-gray-50 dark:bg-slate-700 border border-gray-200 dark:border-slate-600 rounded-md p-3 sm:p-4 max-h-32 sm:max-h-40 overflow-y-auto">
                          <p className="text-sm text-gray-700 dark:text-slate-300 whitespace-pre-wrap">
                            {texts.find(t => t.id === selectedTextId)?.body || 'Metin yükleniyor...'}
                          </p>
                        </div>
                      </div>
                    )}

                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                        <BookIcon size="sm" className="mr-2" />
                        Veya Özel Metin Girin
                      </label>
                      <textarea
                        value={customText}
                        onChange={(e) => {
                          setCustomText(e.target.value);
                          setSelectedTextId('');
                        }}
                        placeholder="Doky analizi yapılacak metni buraya yazın..."
                        className="block w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white dark:bg-slate-800 text-gray-900 dark:text-slate-100"
                        rows={3}
                      />
                      {formErrors.text && (
                        <Error 
                          message={formErrors.text} 
                          type="warning" 
                          size="sm" 
                          showIcon={true}
                        />
                      )}
                    </div>
                  </div>
                </div>

                {/* Submit Button */}
                {hasPermission('analysis:create') && (
                  <div className="flex justify-center">
                    <button
                      onClick={startAnalysis}
                      disabled={isUploading}
                      className="w-full sm:w-auto px-6 py-3 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm flex items-center justify-center"
                    >
                      {isUploading ? (
                        <Loading variant="spinner" size="sm" text="Analiz Ediliyor..." />
                      ) : (
                        <>
                          <AnalysisIcon size="sm" className="mr-2" />
                          Analiz Et
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Toast Messages */}
      {showErrorToast && (
        <ErrorToast 
          message={error || 'Bir hata oluştu'} 
          onDismiss={() => setShowErrorToast(false)} 
        />
      )}
      
      {showSuccessToast && (
        <SuccessToast 
          message="Analiz başlatıldı! Geçmiş Analizler sayfasından takip edebilirsiniz." 
          onDismiss={() => setShowSuccessToast(false)} 
        />
      )}

    </div>
  );
}