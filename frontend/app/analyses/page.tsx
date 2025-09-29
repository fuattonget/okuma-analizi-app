'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, AnalysisSummary } from '@/lib/api';
import { formatTurkishDate } from '@/lib/dateUtils';
import { useAnalysisStore } from '@/lib/store';
import classNames from 'classnames';

export default function AnalysesPage() {
  const router = useRouter();
  const { analyses, setAnalyses, updateAnalysis, startPolling, stopPolling, stopAllPolling } = useAnalysisStore();
  
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'queued' | 'running' | 'done' | 'failed'>('all');

  useEffect(() => {
    loadAnalyses();
    
    // Cleanup polling on unmount
    return () => {
      stopAllPolling();
    };
  }, []);

  const loadAnalyses = useCallback(async () => {
    try {
      setLoading(true);
      const analysesData = await apiClient.getAnalyses(50); // Load more analyses
      setAnalyses(analysesData);
      
      // Start polling for running/queued analyses
      analysesData.forEach(analysis => {
        if (analysis.status === 'running' || analysis.status === 'queued') {
          startPolling(analysis.id, async () => {
            try {
              const updatedAnalysis = await apiClient.getAnalysis(analysis.id);
              updateAnalysis(analysis.id, { status: updatedAnalysis.status });
              
              if (updatedAnalysis.status === 'done' || updatedAnalysis.status === 'failed') {
                // Reload full analysis data
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
  }, [setAnalyses, startPolling, updateAnalysis, stopPolling]);

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      queued: 'bg-gray-100 text-gray-800',
      running: 'bg-yellow-100 text-yellow-800',
      done: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };
    
    return (
      <span className={classNames('badge', statusClasses[status as keyof typeof statusClasses] || 'bg-gray-100 text-gray-800')}>
        {status}
      </span>
    );
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

  if (loading) {
    return (
      <div className="space-y-8">
        {/* Navigation */}
        <div className="flex justify-center space-x-4 mb-8">
          <a href="/" className="btn btn-secondary">Ana Sayfa</a>
          <a href="/analyses" className="btn btn-primary">Geçmiş Analizler</a>
          <a href="/texts" className="btn btn-secondary">Metin Yönetimi</a>
        </div>
        
        <div className="flex justify-center items-center h-64">
          <div className="text-gray-500">Yükleniyor...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Geçmiş Analizler</h1>
        <p className="text-gray-600">Tüm ses dosyası analizlerinizi buradan görüntüleyebilirsiniz</p>
      </div>

      {/* Status Filter */}
      <div className="card">
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
                'btn btn-sm',
                filter === key ? 'btn-primary' : 'btn-secondary'
              )}
            >
              {label} ({count})
            </button>
          ))}
        </div>
      </div>


      {/* Analyses List */}
      <div className="card">
        {filteredAnalyses.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg mb-4">
              {filter === 'all' ? 'Henüz analiz bulunmuyor' : `${filter} durumunda analiz bulunmuyor`}
            </p>
            <a href="/" className="btn btn-primary">
              İlk Analizi Başlat
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAnalyses.map((analysis) => (
              <div
                key={analysis.id}
                onClick={() => router.push(`/analysis/${analysis.id}`)}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-all duration-200 cursor-pointer bg-white"
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="font-semibold text-gray-900 truncate text-lg">
                    {analysis.text_title}
                  </h3>
                  {getStatusBadge(analysis.status)}
                </div>
                
                <div className="space-y-3">
                  <p className="text-sm text-gray-500">
                    <span className="font-medium">Tarih:</span> {formatTurkishDate(analysis.created_at)}
                  </p>
                  
                  {analysis.status === 'done' && (
                    <div className="bg-green-50 p-3 rounded-lg">
                      <div className="text-sm font-medium text-green-800 mb-2">Analiz Sonuçları:</div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-gray-600">WER:</span>
                          <span className="font-medium ml-1">{analysis.summary?.wer?.toFixed(3) || analysis.wer?.toFixed(3) || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Doğruluk:</span>
                          <span className="font-medium ml-1">%{analysis.summary?.accuracy?.toFixed(1) || analysis.accuracy?.toFixed(1) || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">WPM:</span>
                          <span className="font-medium ml-1">{analysis.summary?.wpm?.toFixed(0) || analysis.wpm?.toFixed(0) || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Duraksama:</span>
                          <span className="font-medium ml-1">{analysis.summary?.long_pauses?.count || 0}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {analysis.status === 'running' && (
                    <div className="bg-yellow-50 p-3 rounded-lg">
                      <div className="text-sm text-yellow-800">
                        <div className="animate-pulse">Analiz devam ediyor...</div>
                      </div>
                    </div>
                  )}
                  
                  {analysis.status === 'failed' && (
                    <div className="bg-red-50 p-3 rounded-lg">
                      <div className="text-sm text-red-800">
                        Analiz başarısız oldu
                      </div>
                    </div>
                  )}
                  
                  {analysis.status === 'queued' && (
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <div className="text-sm text-gray-600">
                        Kuyrukta bekliyor...
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <div className="text-xs text-gray-500 text-center">
                    Detayları görmek için tıklayın
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
