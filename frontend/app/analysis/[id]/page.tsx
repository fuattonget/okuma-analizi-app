'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient, AnalysisDetail } from '@/lib/api';
import { tokenizeWithSeparators } from '@/lib/tokenize';
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
    } catch (err) {
      setError('Analiz bulunamadı');
      console.error('Failed to load analysis:', err);
    } finally {
      setLoading(false);
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

  const getEventTypeColor = (type: string) => {
    const colors = {
      correct: 'text-green-600 bg-green-50',
      diff: 'text-yellow-600 bg-yellow-50',
      missing: 'text-red-600 bg-red-50',
      extra: 'text-blue-600 bg-blue-50',
    };
    return colors[type as keyof typeof colors] || 'text-gray-600 bg-gray-50';
  };

  const renderTextWithAnalysis = () => {
    if (!analysis) return null;

    const tokens = tokenizeWithSeparators(analysis.text.body);
    const wordEvents = analysis.word_events;
    const pauseEvents = analysis.pause_events;

    // Create lookup maps
    const wordEventMap = new Map();
    wordEvents.forEach(event => {
      if (event.ref_idx !== undefined) {
        wordEventMap.set(event.ref_idx, event);
      }
    });

    const pauseEventMap = new Map();
    pauseEvents.forEach(pause => {
      pauseEventMap.set(pause.after_word_idx, pause);
    });

    let wordIndex = 0;
    let lastPauseIndex = -1;

    return tokens.map((token, tokenIndex) => {
      if (token.type === 'separator') {
        return <span key={tokenIndex}>{token.content}</span>;
      }

      const wordEvent = wordEventMap.get(wordIndex);
      const pauseEvent = pauseEventMap.get(wordIndex);
      
      const wordElement = (
        <span
          key={tokenIndex}
          className={classNames({
            'token-missing': wordEvent?.type === 'missing',
            'token-diff': wordEvent?.type === 'diff',
          })}
        >
          {token.content}
        </span>
      );

      const elements = [wordElement];

      // Add extra tokens (insertions) after the current word
      if (wordEvent?.type === 'insert' && wordEvent.hyp_token) {
        elements.push(
          <span key={`extra-${tokenIndex}`} className="token-extra">
            [ek: '{wordEvent.hyp_token}']
          </span>
        );
      }

      // Add pause marker
      if (pauseEvent && wordIndex > lastPauseIndex) {
        elements.push(
          <span
            key={`pause-${tokenIndex}`}
            className="pause-mark"
            title={`Duraksama ${pauseEvent.duration_ms.toFixed(0)} ms`}
          >
            ⏸️
          </span>
        );
        lastPauseIndex = wordIndex;
      }

      wordIndex++;
      return elements;
    });
  };

  const getSummaryBreakdown = () => {
    if (!analysis?.summary?.counts) return null;

    const counts = analysis.summary.counts;
    const wordEvents = analysis.word_events;
    
    // Count subtypes
    const subtypeCounts = {
      harf_ek: 0,
      harf_cik: 0,
      degistirme: 0,
      hece_ek: 0,
      hece_cik: 0,
    };

    wordEvents.forEach(event => {
      if (event.subtype && subtypeCounts.hasOwnProperty(event.subtype)) {
        subtypeCounts[event.subtype as keyof typeof subtypeCounts]++;
      }
    });

    return {
      correct: counts.correct || 0,
      errors: (counts.diff || 0) + (counts.missing || 0) + (counts.extra || 0),
      missing: counts.missing || 0,
      extra: counts.extra || 0,
      diff: counts.diff || 0,
      subtypeCounts,
      longPauses: analysis.summary.long_pauses?.count || 0,
    };
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
        {getStatusBadge(analysis.status)}
      </div>

      {/* Analysis Info */}
      <div className="card">
        <h1 className="text-xl font-semibold mb-4">{analysis.text.title}</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-sm text-gray-600">Oluşturulma</p>
            <p className="font-medium">{new Date(analysis.created_at).toLocaleString('tr-TR')}</p>
          </div>
          {analysis.started_at && (
            <div>
              <p className="text-sm text-gray-600">Başlama</p>
              <p className="font-medium">{new Date(analysis.started_at).toLocaleString('tr-TR')}</p>
            </div>
          )}
          {analysis.finished_at && (
            <div>
              <p className="text-sm text-gray-600">Bitiş</p>
              <p className="font-medium">{new Date(analysis.finished_at).toLocaleString('tr-TR')}</p>
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
        {analysis.audio_url && (
          <div className="mb-6">
            <p className="text-sm font-medium text-gray-700 mb-2">Ses Dosyası</p>
            <audio controls className="w-full">
              <source src={analysis.audio_url} type="audio/mpeg" />
              Tarayıcınız ses dosyasını desteklemiyor.
            </audio>
          </div>
        )}

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
        <>
          {/* Summary Stats */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Analiz Sonuçları</h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {analysis.summary.wer?.toFixed(3) || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">WER</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {analysis.summary.accuracy?.toFixed(1) || 'N/A'}%
                </p>
                <p className="text-sm text-gray-600">Doğruluk</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">
                  {analysis.summary.wpm?.toFixed(1) || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">WPM</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">
                  {analysis.summary.long_pauses?.count || 0}
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

                      {/* Subtype Breakdown */}
                      <div>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Kelime Farklılık Türleri</h4>
                        <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                          {Object.entries(breakdown.subtypeCounts).map(([subtype, count]) => (
                            <div key={subtype} className="text-center">
                              <p className="text-sm font-semibold text-gray-800">{count}</p>
                              <p className="text-xs text-gray-600 capitalize">
                                {subtype.replace('_', ' ')}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>

          {/* Word Events */}
          {analysis.word_events.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Kelime Analizi</h2>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {analysis.word_events.map((event, index) => (
                  <div
                    key={index}
                    className={classNames(
                      'flex items-center justify-between p-3 rounded-md border',
                      getEventTypeColor(event.type)
                    )}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{event.ref_token || '_'}</span>
                        <span className="text-gray-400">→</span>
                        <span className="font-medium">{event.hyp_token || '_'}</span>
                        {event.subtype && (
                          <span className="text-xs px-2 py-1 rounded bg-white bg-opacity-50">
                            {event.subtype}
                          </span>
                        )}
                      </div>
                      {event.start_ms !== undefined && event.end_ms !== undefined && (
                        <p className="text-xs text-gray-500 mt-1">
                          {event.start_ms.toFixed(0)}ms - {event.end_ms.toFixed(0)}ms
                        </p>
                      )}
                    </div>
                    <span className="text-sm font-medium capitalize">
                      {event.type}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Pause Events */}
          {analysis.pause_events.length > 0 && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Duraksama Analizi</h2>
              <div className="space-y-2">
                {analysis.pause_events.map((pause, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-md border"
                  >
                    <div>
                      <p className="font-medium">
                        Kelime {pause.after_word_idx} sonrası
                      </p>
                      <p className="text-sm text-gray-600">
                        {pause.start_ms.toFixed(0)}ms - {pause.end_ms.toFixed(0)}ms
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-orange-600">
                        {pause.duration_ms.toFixed(0)}ms
                      </p>
                      <p className="text-xs text-gray-500">Süre</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
      
      {/* Debug Components */}
      <DebugButton />
      <DebugPanel />
    </div>
  );
}
