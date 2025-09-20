'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient, AnalysisDetail, WordEvent, PauseEvent, Metrics } from '@/lib/api';
import { tokenizeWithSeparators } from '@/lib/tokenize';
import { formatTurkishDate } from '@/lib/dateUtils';
import classNames from 'classnames';
import DebugButton from '@/components/DebugButton';
import DebugPanel from '@/components/DebugPanel';

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioLoading, setAudioLoading] = useState(false);
  
  // Event data states
  const [wordEvents, setWordEvents] = useState<WordEvent[]>([]);
  const [pauseEvents, setPauseEvents] = useState<PauseEvent[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'summary' | 'words' | 'pauses'>('summary');
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (params.id) {
      loadAnalysis(params.id as string);
    }
  }, [params.id]);

  const loadAnalysis = async (id: string) => {
    try {
      setLoading(true);
      const analysisData = await apiClient.getAnalysis(id);
      setAnalysis(analysisData);
      
      // Load events if analysis is completed
      if (analysisData.status === 'done') {
        loadEvents(id);
      }
    } catch (err) {
      setError('Analiz bulunamadı');
      console.error('Failed to load analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEvents = async (analysisId: string) => {
    try {
      setEventsLoading(true);
      const [wordEventsData, pauseEventsData, metricsData] = await Promise.all([
        apiClient.getWordEvents(analysisId),
        apiClient.getPauseEvents(analysisId),
        apiClient.getMetrics(analysisId)
      ]);
      
      setWordEvents(wordEventsData);
      setPauseEvents(pauseEventsData);
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setEventsLoading(false);
    }
  };

  const loadAudioUrl = async (analysisId: string) => {
    try {
      setAudioLoading(true);
      const audioData = await apiClient.getAnalysisAudioUrl(analysisId, 1); // 1 hour expiration
      setAudioUrl(audioData.signed_url);
    } catch (err) {
      console.error('Failed to load audio URL:', err);
      setError('Ses dosyası yüklenemedi');
    } finally {
      setAudioLoading(false);
    }
  };

  const downloadAnalysisAsJSON = async (analysisId: string) => {
    try {
      setDownloading(true);
      const analysisData = await apiClient.getAnalysisExport(analysisId);
      
      // Create a blob with the JSON data
      const jsonString = JSON.stringify(analysisData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });
      
      // Create a download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `analysis_${analysisId}.json`;
      
      // Trigger the download
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up the URL object
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download analysis:', err);
      setError('Analiz indirilemedi');
    } finally {
      setDownloading(false);
    }
  };

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


  const renderTextWithAnalysis = () => {
    if (!analysis) return null;

    const tokens = tokenizeWithSeparators(analysis.text.body);

    return tokens.map((token, tokenIndex) => {
      if (token.type === 'separator') {
        return <span key={tokenIndex}>{token.content}</span>;
      }

      return (
        <span key={tokenIndex}>
          {token.content}
        </span>
      );
    });
  };

  const getSummaryBreakdown = () => {
    if (!analysis?.summary?.counts) return null;

    const counts = analysis.summary.counts;

    return {
      correct: counts.correct || 0,
      errors: (counts.diff || 0) + (counts.missing || 0) + (counts.extra || 0),
      missing: counts.missing || 0,
      extra: counts.extra || 0,
      diff: counts.diff || 0,
      longPauses: analysis.summary.long_pauses?.count || 0,
    };
  };

  const getEventTypeColor = (type: string) => {
    const colors = {
      correct: 'text-green-600 bg-green-50',
      missing: 'text-red-600 bg-red-50',
      extra: 'text-blue-600 bg-blue-50',
      diff: 'text-yellow-600 bg-yellow-50',
      substitution: 'text-orange-600 bg-orange-50'
    };
    return colors[type as keyof typeof colors] || 'text-gray-600 bg-gray-50';
  };

  const getPauseClassColor = (class_: string) => {
    const colors = {
      short: 'text-green-600 bg-green-50',
      medium: 'text-yellow-600 bg-yellow-50',
      long: 'text-orange-600 bg-orange-50',
      very_long: 'text-red-600 bg-red-50'
    };
    return colors[class_ as keyof typeof colors] || 'text-gray-600 bg-gray-50';
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms.toFixed(0)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500">Yükleniyor...</div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error || 'Analiz bulunamadı'}</p>
        <button
          onClick={() => router.push('/')}
          className="btn btn-primary"
        >
          Ana Sayfaya Dön
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => router.push('/')}
          className="btn btn-secondary"
        >
          ← Geri
        </button>
        <div className="flex items-center space-x-3">
          {analysis.status === 'done' && (
            <button
              onClick={() => downloadAnalysisAsJSON(analysis.id)}
              disabled={downloading}
              className="btn btn-primary btn-sm"
            >
              {downloading ? 'İndiriliyor...' : 'Sonucu JSON Olarak İndir'}
            </button>
          )}
          {getStatusBadge(analysis.status)}
        </div>
      </div>

      {/* Analysis Info */}
      <div className="card">
        <h1 className="text-xl font-semibold mb-4">{analysis.text.title}</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-sm text-gray-600">Oluşturulma</p>
            <p className="font-medium">{formatTurkishDate(analysis.created_at)}</p>
          </div>
          {analysis.started_at && (
            <div>
              <p className="text-sm text-gray-600">Başlama</p>
              <p className="font-medium">{formatTurkishDate(analysis.started_at)}</p>
            </div>
          )}
          {analysis.finished_at && (
            <div>
              <p className="text-sm text-gray-600">Bitiş</p>
              <p className="font-medium">{formatTurkishDate(analysis.finished_at)}</p>
            </div>
          )}
        </div>

        {analysis.error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <p className="text-red-800 font-medium">Hata:</p>
            <p className="text-red-700">{analysis.error}</p>
          </div>
        )}

        {/* Audio Player */}
        <div className="mb-6">
          <p className="text-sm font-medium text-gray-700 mb-2">Ses Dosyası</p>
          {audioUrl ? (
            <audio controls className="w-full">
              <source src={audioUrl} type="audio/mpeg" />
              Tarayıcınız ses dosyasını desteklemiyor.
            </audio>
          ) : (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => loadAudioUrl(analysis.id)}
                disabled={audioLoading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {audioLoading ? 'Yükleniyor...' : 'Ses Dosyasını Yükle'}
              </button>
              <span className="text-sm text-gray-500">
                (1 saat geçerli güvenli bağlantı)
              </span>
            </div>
          )}
        </div>

        {/* Reference Text with Analysis */}
        <div className="mb-6">
          <p className="text-sm font-medium text-gray-700 mb-2">Hedef Metin</p>
          <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
            <div className="text-gray-800 leading-relaxed">
              {renderTextWithAnalysis()}
            </div>
          </div>
        </div>
      </div>

      {/* Results */}
      {analysis.status === 'done' && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Analiz Sonuçları</h2>
          
          {/* Tab Navigation */}
          <div className="flex space-x-1 mb-6 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('summary')}
              className={classNames(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'summary'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              Özet
            </button>
            <button
              onClick={() => setActiveTab('words')}
              className={classNames(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'words'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              Kelime Olayları ({wordEvents.length})
            </button>
            <button
              onClick={() => setActiveTab('pauses')}
              className={classNames(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'pauses'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              )}
            >
              Duraksama Olayları ({pauseEvents.length})
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'summary' && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {metrics?.wer?.toFixed(3) || analysis.summary.wer?.toFixed(3) || 'N/A'}
                  </p>
                  <p className="text-sm text-gray-600">WER</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {metrics?.accuracy?.toFixed(1) || analysis.summary.accuracy?.toFixed(1) || 'N/A'}%
                  </p>
                  <p className="text-sm text-gray-600">Doğruluk</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    {metrics?.wpm?.toFixed(1) || analysis.summary.wpm?.toFixed(1) || 'N/A'}
                  </p>
                  <p className="text-sm text-gray-600">WPM</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-orange-600">
                    {metrics?.long_pauses?.count || analysis.summary.long_pauses?.count || 0}
                  </p>
                  <p className="text-sm text-gray-600">Uzun Duraksama</p>
                </div>
              </div>

              {/* Enhanced Summary */}
              {(() => {
                const breakdown = getSummaryBreakdown();
                if (!breakdown) return null;

                return (
                  <div className="border-t pt-4">
                    <div 
                      className="flex items-center justify-between cursor-pointer hover:bg-gray-50 p-2 rounded"
                      onClick={() => setSummaryExpanded(!summaryExpanded)}
                    >
                      <div className="flex items-center gap-4">
                        <span className="text-sm font-medium text-gray-700">
                          Doğru: <span className="text-green-600 font-semibold">{breakdown.correct}</span> | 
                          Hatalı: <span className="text-red-600 font-semibold">{breakdown.errors}</span>
                        </span>
                      </div>
                      <span className="text-gray-400">
                        {summaryExpanded ? '▲' : '▼'}
                      </span>
                    </div>
                    
                    {summaryExpanded && (
                      <div className="mt-4 space-y-4">
                        {/* Error Breakdown */}
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 mb-2">Hata Detayları</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center">
                              <p className="text-lg font-semibold text-red-600">{breakdown.missing}</p>
                              <p className="text-xs text-gray-600">Eksik</p>
                            </div>
                            <div className="text-center">
                              <p className="text-lg font-semibold text-blue-600">{breakdown.extra}</p>
                              <p className="text-xs text-gray-600">Fazla</p>
                            </div>
                            <div className="text-center">
                              <p className="text-lg font-semibold text-yellow-600">{breakdown.diff}</p>
                              <p className="text-xs text-gray-600">Kelimede Farklılık</p>
                            </div>
                            <div className="text-center">
                              <p className="text-lg font-semibold text-orange-600">{breakdown.longPauses}</p>
                              <p className="text-xs text-gray-600">Uzun Duraksama</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })()}
            </>
          )}

          {activeTab === 'words' && (
            <div>
              {eventsLoading ? (
                <div className="text-center py-8">
                  <div className="text-gray-500">Kelime olayları yükleniyor...</div>
                </div>
              ) : wordEvents.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-500">Kelime olayı bulunamadı</div>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {wordEvents.map((event, index) => (
                    <div key={event.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-mono text-gray-500 w-8">#{event.position}</span>
                        <div className="flex items-center space-x-2">
                          {event.ref_token && (
                            <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm">
                              {event.ref_token}
                            </span>
                          )}
                          {event.hyp_token && event.hyp_token !== event.ref_token && (
                            <>
                              <span className="text-gray-400">→</span>
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                                {event.hyp_token}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={classNames('px-2 py-1 rounded text-xs font-medium', getEventTypeColor(event.type))}>
                          {event.type}
                        </span>
                        {event.char_diff && (
                          <span className="text-xs text-gray-500">
                            {event.char_diff > 0 ? '+' : ''}{event.char_diff} char
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'pauses' && (
            <div>
              {eventsLoading ? (
                <div className="text-center py-8">
                  <div className="text-gray-500">Duraksama olayları yükleniyor...</div>
                </div>
              ) : pauseEvents.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-500">Duraksama olayı bulunamadı</div>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {pauseEvents.map((event, index) => (
                    <div key={event.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-sm font-mono text-gray-500 w-8">#{event.after_position}</span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-700">
                            {formatDuration(event.start_ms)} - {formatDuration(event.end_ms)}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className={classNames('px-2 py-1 rounded text-xs font-medium', getPauseClassColor(event.class_))}>
                          {event.class_}
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                          {formatDuration(event.duration_ms)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
      
      {/* Debug Components */}
      <DebugButton />
      <DebugPanel />
    </div>
  );
}
