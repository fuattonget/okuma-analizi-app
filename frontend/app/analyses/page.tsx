'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, AnalysisSummary, Student } from '@/lib/api';
import { formatTurkishDate } from '@/lib/dateUtils';
import { useAnalysisStore } from '@/lib/store';
import { useAuth } from '@/lib/useAuth';
import { useRoles } from '@/lib/useRoles';
import classNames from 'classnames';
import Navigation from '@/components/Navigation';
import Breadcrumbs from '@/components/Breadcrumbs';
import { themeColors, combineThemeClasses, componentClasses } from '@/lib/theme';

export default function AnalysesPage() {
  const router = useRouter();
  const { analyses, setAnalyses, updateAnalysis, startPolling, stopPolling, stopAllPolling } = useAnalysisStore();
  const { isAuthenticated, isAuthLoading } = useAuth();
  const { hasPermission } = useRoles();
  
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'queued' | 'running' | 'done' | 'failed'>('all');
  const [students, setStudents] = useState<Student[]>([]);

  const loadAnalyses = useCallback(async () => {
    // Check if user has permission to view all analyses
    if (!hasPermission('analysis:read_all')) {
      console.log('⚠️ User does not have permission to view all analyses');
      setLoading(false);
      return;
    }
    
    try {
      setLoading(true);
      console.log('🔄 Loading analyses...');
      const analysesData = await apiClient.getAnalyses(50);
      console.log('📊 Analyses data:', analysesData);
      console.log('📊 First analysis student_id:', analysesData[0]?.student_id);
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
        } finally {
      setLoading(false);
    }
  }, [setAnalyses, startPolling, updateAnalysis, stopPolling, hasPermission]);

  const loadStudents = useCallback(async () => {
    try {
      console.log('🔄 Loading students...');
      const response = await apiClient.getStudents();
      console.log('👥 Students response:', response);
      const studentsData = Array.isArray(response) ? response : response.students || [];
      console.log('👥 Students data:', studentsData);
      console.log('👥 Students count:', studentsData?.length || 0);
      setStudents(studentsData);
    } catch (error) {
      console.error('Failed to load students:', error);
      setStudents([]);
    }
  }, []);

  // Handle token expiration and redirect
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      console.log('🔍 AnalysesPage: User not authenticated, redirecting to login');
      router.push('/login');
    }
  }, [isAuthenticated, isAuthLoading, router]);

  useEffect(() => {
    if (isAuthenticated) {
      loadAnalyses();
      loadStudents();
    }
    
    // Cleanup polling on unmount
    return () => {
      stopAllPolling();
    };
  }, [isAuthenticated, loadAnalyses, loadStudents, stopAllPolling]);

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      queued: 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300',
      running: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300',
      done: 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300',
      failed: 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300',
    };
    
    return (
      <span className={classNames('px-2 py-1 text-xs font-medium rounded-full', statusClasses[status as keyof typeof statusClasses] || 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300')}>
        {status === 'queued' && 'Bekleyen'}
        {status === 'running' && 'Çalışıyor'}
        {status === 'done' && 'Tamamlandı'}
        {status === 'failed' && 'Başarısız'}
      </span>
    );
  };

  const getStudentInfo = (studentId?: string) => {
    if (!studentId) return null;
    const student = students.find(s => s.id === studentId);
    if (!student) return null;
    
    return (
      <div className="flex items-center space-x-2">
        <div className="w-6 h-6 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center flex-shrink-0">
          <span className="text-xs font-bold text-blue-600 dark:text-blue-300">
            {student.first_name.charAt(0)}{student.last_name.charAt(0)}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <span className="text-sm text-gray-700 dark:text-slate-300 truncate block">
            {student.first_name} {student.last_name}
          </span>
          <span className="text-xs text-gray-500 dark:text-slate-400">
            ({student.grade === 0 ? 'Diğer' : `${student.grade}. Sınıf`})
          </span>
        </div>
      </div>
    );
  };

  const getAnalysisTitle = (analysis: AnalysisSummary) => {
    console.log('🔍 getAnalysisTitle called for analysis:', analysis.id, 'student_id:', analysis.student_id);
    console.log('👥 Available students:', students.length, students.map(s => ({ id: s.id, name: `${s.first_name} ${s.last_name}` })));
    if (analysis.student_id) {
      const student = students.find(s => s.id === analysis.student_id);
      console.log('👤 Found student:', student);
      if (student) {
        return `${student.first_name} ${student.last_name} - ${analysis.text_title}`;
      }
    }
    return analysis.text_title;
  };

  const filteredAnalyses = analyses.filter(analysis => {
    if (filter === 'all') return true;
    return analysis.status === filter;
  });

  const getStatusCounts = () => {
    const counts = {
      all: analyses.length,
      queued: analyses.filter(a => a.status === 'queued').length,
      running: analyses.filter(a => a.status === 'running').length,
      done: analyses.filter(a => a.status === 'done').length,
      failed: analyses.filter(a => a.status === 'failed').length,
    };
    return counts;
  };

  const statusCounts = getStatusCounts();

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
      console.log('🔍 AnalysesPage: Showing auth loading spinner');
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Kimlik doğrulanıyor...</p>
          </div>
        </div>
      );
    }
    
    console.log('🔍 AnalysesPage: Not authenticated, redirecting to login');
    return null; // Will redirect via useEffect
  }

  // Check if user has permission to view all analyses
  if (!hasPermission('analysis:read_all')) {
    return (
      <div className={combineThemeClasses('min-h-screen', themeColors.background.primary)}>
        <Navigation />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Breadcrumbs items={[{ label: 'Analizler', href: '/analyses' }]} />
          
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-6 rounded-lg shadow-sm mt-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-yellow-800 mb-2">
                  Yetki Gerekiyor
                </h3>
                <div className="text-yellow-700">
                  <p className="mb-2">
                    Tüm analizleri görüntülemek için <strong className="font-semibold">"Tüm Analizleri Görüntüle"</strong> yetkisine ihtiyacınız var.
                  </p>
                  <p className="text-sm text-yellow-600 mt-2">
                    Öğrenci analizlerini görüntülemek için öğrenci detay sayfasını kullanabilirsiniz.
                  </p>
                  <p className="text-xs text-yellow-600 mt-2">
                    Bu yetkiyi almak için sistem yöneticinizle iletişime geçin.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
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
          {/* Breadcrumbs */}
          <Breadcrumbs />
          
          {/* Status Filter */}
          <div className="bg-white dark:bg-slate-800 shadow rounded-lg p-4 sm:p-6 border border-gray-200 dark:border-slate-700">
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                { key: 'all', label: 'Tümü', count: statusCounts.all },
                { key: 'queued', label: 'Bekleyen', count: statusCounts.queued },
                { key: 'running', label: 'Çalışıyor', count: statusCounts.running },
                { key: 'done', label: 'Tamamlandı', count: statusCounts.done },
                { key: 'failed', label: 'Başarısız', count: statusCounts.failed },
              ].map(({ key, label, count }) => (
                <button
                  key={key}
                  onClick={() => setFilter(key as any)}
                  className={classNames(
                    'px-3 sm:px-4 py-2 rounded-md text-sm font-medium transition-colors',
                    filter === key 
                      ? 'bg-indigo-600 text-white' 
                      : 'bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-slate-300 hover:bg-gray-200 dark:hover:bg-slate-600'
                  )}
                >
                  <span className="hidden sm:inline">{label}</span>
                  <span className="sm:hidden">{label.split(' ')[0]}</span>
                  <span className="ml-1">({count})</span>
                </button>
              ))}
            </div>
          </div>

          {/* Analyses List */}
          {filteredAnalyses.length === 0 ? (
            <div className="bg-white dark:bg-slate-800 shadow rounded-lg p-6 sm:p-8 text-center border border-gray-200 dark:border-slate-700">
              <div className="text-gray-500 dark:text-slate-400 text-base sm:text-lg">
                {filter === 'all' ? 'Henüz analiz bulunmuyor' : `${filter} durumunda analiz bulunmuyor`}
              </div>
            </div>
          ) : (
            <div className="grid gap-3 sm:gap-4">
              {filteredAnalyses.map((analysis) => (
                <div
                  key={analysis.id}
                  onClick={() => router.push(`/analyses/${analysis.id}`)}
                  className="bg-white dark:bg-slate-800 shadow rounded-lg p-4 sm:p-6 cursor-pointer hover:shadow-md transition-shadow border border-gray-200 dark:border-slate-700"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between space-y-3 sm:space-y-0">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-base sm:text-lg font-medium text-gray-900 dark:text-slate-100 truncate">
                        {getAnalysisTitle(analysis)}
                      </h3>
                      <div className="flex flex-col sm:flex-row sm:items-center space-y-1 sm:space-y-0 sm:space-x-4 mt-1">
                        <p className="text-sm text-gray-500 dark:text-slate-400">
                          {formatTurkishDate(analysis.created_at)}
                        </p>
                        {getStudentInfo(analysis.student_id)}
                      </div>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
                      {getStatusBadge(analysis.status)}
                      {analysis.status === 'running' && (
                        <div className="text-sm text-gray-600 dark:text-slate-400 flex items-center">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600 inline-block mr-2"></div>
                          İşleniyor...
                        </div>
                      )}
                      {analysis.status === 'queued' && (
                        <div className="text-sm text-gray-600 dark:text-slate-400">
                          Kuyrukta bekliyor...
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="mt-4 pt-3 border-t border-gray-100 dark:border-slate-600">
                    <div className="text-xs text-gray-500 dark:text-slate-400 text-center">
                      Detayları görmek için tıklayın
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}