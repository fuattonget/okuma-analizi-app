'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { apiClient, AnalysisDetail, WordEvent, PauseEvent, Metrics, AnalysisExport } from '@/lib/api';
import { tokenizeWithSeparators } from '@/lib/tokenize';
import { formatTurkishDate } from '@/lib/dateUtils';
import classNames from 'classnames';

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [exportData, setExportData] = useState<AnalysisExport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioLoading, setAudioLoading] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  
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
      
      // Load export data if analysis is completed
      if (analysisData.status === 'done') {
        await loadExportData(id);
      }
    } catch (err) {
      setError('Analiz bulunamadı');
      console.error('Failed to load analysis:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadExportData = async (analysisId: string) => {
    try {
      setEventsLoading(true);
      const exportData = await apiClient.getAnalysisExport(analysisId);
      setExportData(exportData);
      
      // Set events and pauses from export data
      setWordEvents(exportData.events);
      setPauseEvents(exportData.pauses);
      
      console.log('Export data loaded:', {
        hasTranscript: !!exportData.transcript,
        transcriptLength: exportData.transcript?.length || 0,
        transcriptPreview: exportData.transcript?.substring(0, 50)
      });
      
      // Create metrics object from export data
      const metricsData: Metrics = {
        analysis_id: exportData.analysis_id,
        counts: exportData.summary.counts,
        wer: exportData.summary.wer,
        accuracy: exportData.summary.accuracy,
        wpm: exportData.summary.wpm,
        long_pauses: exportData.summary.long_pauses,
        error_types: exportData.summary.error_types
      };
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load export data:', err);
      // Fallback to individual API calls if export fails
      await loadEvents(analysisId);
    } finally {
      setEventsLoading(false);
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

  const handleWordClick = (event: WordEvent) => {
    if (!audioRef.current || !event.timing?.start_ms) {
      console.log('Audio element or timing not available', {
        hasAudio: !!audioRef.current,
        hasTiming: !!event.timing,
        timing: event.timing
      });
      return;
    }

    const startTime = event.timing.start_ms / 1000; // Convert ms to seconds
    audioRef.current.currentTime = startTime;
    audioRef.current.play();
    
    console.log(`Jumped to word "${event.hyp_token || event.ref_token}" at ${startTime}s`);
  };

  const downloadAnalysisAsJSON = async (analysisId: string) => {
    try {
      setDownloading(true);
      const analysisData = exportData || await apiClient.getAnalysisExport(analysisId);
      
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


  const getSubTypeLabel = (subType: string): string => {
    const labels: { [key: string]: string } = {
      'harf_ekleme': 'Harf ekledi',
      'harf_eksiltme': 'Harf eksik',
      'harf_değiştirme': 'Harf değiştirdi',
      'hece_ekleme': 'Hece ekledi',
      'hece_eksiltme': 'Hece eksik',
      'tamamen_farklı': 'Tamamen farklı kelime',
    };
    return labels[subType] || '';
  };

  const getRepetitionLabel = (subType: string): string => {
    const labels: { [key: string]: string } = {
      'exact_match': 'Aynı kelimeyi tekrar etti',
      'enhanced_pattern': 'Tekrarlama yaptı',
      'similar_extra': 'Benzer kelimeyi tekrar etti',
    };
    return labels[subType] || 'Tekrar etti';
  };

  const renderTextWithAnalysis = () => {
    if (!analysis) return null;

    const tokens = tokenizeWithSeparators(analysis.text.body);
    const events = exportData?.events || wordEvents;

    // Create a map of ref_token positions to events
    const refTokenToEvent: { [key: number]: WordEvent } = {};
    events.forEach((event) => {
      if (event.ref_idx !== undefined && event.ref_idx >= 0) {
        refTokenToEvent[event.ref_idx] = event;
      }
    });

    let currentRefIdx = 0;

    return tokens.map((token, tokenIndex) => {
      if (token.type === 'separator') {
        return <span key={tokenIndex}>{token.content}</span>;
      }

      // Get the event for this token
      const event = refTokenToEvent[currentRefIdx];
      currentRefIdx++;

      // Determine styling based on event type
      let className = '';
      let title = '';
      
      if (event) {
        switch (event.type) {
          case 'correct':
            // Don't color correct words
            className = '';
            title = '';
            break;
          case 'missing':
            className = 'bg-red-100 text-red-900 px-1 rounded';
            const subTypeText = event.sub_type ? ` (${getSubTypeLabel(event.sub_type)})` : '';
            title = `Atlandı${subTypeText}`;
            break;
          case 'substitution':
            className = 'bg-orange-100 text-orange-900 px-1 rounded border-b-2 border-orange-400';
            const subLabel = getSubTypeLabel(event.sub_type || '');
            title = `Yanlış okundu: "${event.ref_token}" yerine "${event.hyp_token}" dedi${subLabel ? ` • ${subLabel}` : ''}`;
            break;
          case 'extra':
            // Extra tokens don't have ref_token, will be shown separately
            className = '';
            break;
          case 'repetition':
            // Repetitions will be shown on hypothesis side
            className = '';
            break;
          default:
            className = '';
        }
      }

      const tooltipId = `ref-tooltip-${tokenIndex}`;
      
      return (
        <span 
          key={tokenIndex}
          className={`${className} ${title ? 'cursor-help relative' : ''} ${event?.type === 'missing' ? 'line-through decoration-2 decoration-red-600' : ''} ${event ? 'cursor-pointer hover:bg-yellow-100' : ''}`}
          onClick={() => event && handleWordClick(event)}
          onMouseEnter={() => {
            if (title) {
              const tooltip = document.getElementById(tooltipId);
              console.log('Tooltip hover (reference):', tooltipId, tooltip);
              if (tooltip) {
                tooltip.style.opacity = '1';
                tooltip.style.visibility = 'visible';
                console.log('Tooltip style set:', tooltip.style.opacity, tooltip.style.visibility);
              }
            }
          }}
          onMouseLeave={() => {
            if (title) {
              const tooltip = document.getElementById(tooltipId);
              if (tooltip) {
                tooltip.style.opacity = '0';
                tooltip.style.visibility = 'hidden';
              }
            }
          }}
        >
          {token.content}
          {title && (
            <span 
              id={tooltipId}
              className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap shadow-lg transition-opacity pointer-events-none"
              style={{
                opacity: 0,
                visibility: 'hidden',
                zIndex: 9999
              }}
            >
              {title}
              <span className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></span>
            </span>
          )}
        </span>
      );
    });
  };

  const renderTranscriptWithAnalysis = () => {
    if (!exportData?.transcript) {
      console.log('No transcript in exportData');
      return null;
    }

    const events = exportData.events || wordEvents;
    
    // Build ordered list of all events (including missing ones)
    // Sort by hyp_idx, but also include missing events
    const sortedEvents = [...events].sort((a, b) => {
      const aIdx = a.hyp_idx !== undefined ? a.hyp_idx : (a.ref_idx || 0) + 1000;
      const bIdx = b.hyp_idx !== undefined ? b.hyp_idx : (b.ref_idx || 0) + 1000;
      return aIdx - bIdx;
    });

    const rendered: JSX.Element[] = [];
    let wordIndex = 0;

    sortedEvents.forEach((event, eventIdx) => {
      let className = '';
      let title = '';
      let displayText = '';
      let isMissing = false;

      switch (event.type) {
        case 'correct':
          displayText = event.hyp_token || '';
          className = '';
          title = `Doğru okundu: "${event.hyp_token}"`;
          break;
        case 'missing':
          // Show missing word as placeholder
          displayText = event.ref_token || '';
          className = 'bg-red-100 text-red-900 px-1 rounded italic';
          title = `Atlanmış kelime: "${event.ref_token}"`;
          isMissing = true;
          break;
        case 'extra':
          displayText = event.hyp_token || '';
          className = 'bg-blue-100 text-blue-900 px-1 rounded border-b-2 border-blue-400';
          title = `Fazladan söyledi: "${event.hyp_token}"`;
          break;
        case 'substitution':
          displayText = event.hyp_token || '';
          className = 'bg-orange-100 text-orange-900 px-1 rounded border-b-2 border-orange-400';
          const subLabel = getSubTypeLabel(event.sub_type || '');
          title = `Yanlış okundu: "${event.ref_token}" yerine "${event.hyp_token}" dedi${subLabel ? ` • ${subLabel}` : ''}`;
          break;
        case 'repetition':
          displayText = event.hyp_token || '';
          className = 'bg-purple-100 text-purple-900 px-1 rounded border-b-2 border-purple-400';
          const repLabel = getRepetitionLabel(event.sub_type || '');
          title = `Tekrar etti: "${event.hyp_token}"${repLabel ? ` • ${repLabel}` : ''}`;
          break;
        default:
          displayText = event.hyp_token || event.ref_token || '';
      }

      // Only render if we have displayText
      if (displayText) {
        const tooltipId = `tooltip-${eventIdx}`;  // eventIdx kullan, wordIndex değil
        
        rendered.push(
          <span 
            key={`word-${eventIdx}`}
            className={`${className} ${title ? 'cursor-help relative' : ''} ${isMissing ? 'line-through decoration-2 decoration-red-600' : ''} ${event.timing?.start_ms ? 'cursor-pointer hover:bg-yellow-100' : ''}`}
            onClick={() => handleWordClick(event)}
            onMouseEnter={() => {
              if (title) {
                const tooltip = document.getElementById(tooltipId);
                console.log('Tooltip hover (transcript):', tooltipId, tooltip);
                if (tooltip) {
                  tooltip.style.opacity = '1';
                  tooltip.style.visibility = 'visible';
                  console.log('Tooltip style set:', tooltip.style.opacity, tooltip.style.visibility);
                }
              }
            }}
            onMouseLeave={() => {
              if (title) {
                const tooltip = document.getElementById(tooltipId);
                if (tooltip) {
                  tooltip.style.opacity = '0';
                  tooltip.style.visibility = 'hidden';
                }
              }
            }}
        >
          <span className={isMissing ? 'opacity-50' : ''}>
            {displayText}
          </span>
          {title && (
            <span 
              id={tooltipId}
              className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg whitespace-nowrap shadow-lg transition-opacity pointer-events-none"
              style={{
                opacity: 0,
                visibility: 'hidden',
                zIndex: 9999
              }}
            >
              {title}
              <span className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900"></span>
            </span>
          )}
        </span>
        );
        
        // Add space after word (except for last word)
        if (eventIdx < sortedEvents.length - 1) {
          rendered.push(<span key={`space-${eventIdx}`}> </span>);
        }
      }
    });

    return rendered;
  };

  const getSummaryBreakdown = () => {
    // Use export data if available, otherwise fall back to analysis summary
    const summary = exportData?.summary || analysis?.summary;
    if (!summary?.counts) return null;

    const counts = summary.counts;

    const breakdown = {
      correct: counts.correct || 0,
      errors: (counts.substitution || 0) + (counts.missing || 0) + (counts.extra || 0) + (counts.repetition || 0),
      missing: counts.missing || 0,
      extra: counts.extra || 0,
      substitution: counts.substitution || 0,
      repetition: counts.repetition || 0,
      longPauses: summary.long_pauses?.count || 0,
    };
    return breakdown;
  };

  const getEventTypeColor = (type: string) => {
    const colors = {
      correct: 'text-green-600 bg-green-50',
      missing: 'text-red-600 bg-red-50',
      extra: 'text-blue-600 bg-blue-50',
      diff: 'text-yellow-600 bg-yellow-50',
      substitution: 'text-orange-600 bg-orange-50',
      repetition: 'text-purple-600 bg-purple-50'
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
          onClick={() => router.push('/analyses')}
          className="btn btn-primary"
        >
          Geçmiş Analizlere Dön
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => router.push('/analyses')}
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
            <audio ref={audioRef} controls className="w-full">
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

        {/* Transcript Text - STT Sonucu */}
        {exportData?.transcript && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-medium text-gray-700">
                📝 Okunan Metin (STT Sonucu)
              </p>
              <div className="flex items-center space-x-2 text-xs">
                <span className="bg-orange-100 text-orange-900 px-2 py-1 rounded">🔄 Değiştirme</span>
                <span className="bg-blue-100 text-blue-900 px-2 py-1 rounded">➕ Fazla</span>
                <span className="bg-purple-100 text-purple-900 px-2 py-1 rounded">🔁 Tekrar</span>
                <span className="bg-red-100 text-red-900 px-2 py-1 rounded opacity-50 italic line-through decoration-2 decoration-red-600">❌ Atlandı</span>
              </div>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="text-gray-800 leading-relaxed">
                {renderTranscriptWithAnalysis()}
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              💡 Renklerin üzerine gelin detayları görün • 🎵 Kelimelere tıklayın ses dosyasında o bölüme gidin
            </p>
          </div>
        )}

        {/* Reference Text - Hedef Metin */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-700">
              🎯 Hedef Metin (Okunması Gereken)
            </p>
            <div className="flex items-center space-x-2 text-xs">
              <span className="bg-orange-100 text-orange-900 px-2 py-1 rounded">🔄 Değiştirme</span>
              <span className="bg-red-100 text-red-900 px-2 py-1 rounded line-through decoration-2 decoration-red-600">❌ Atlandı</span>
            </div>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
            <div className="text-gray-800 leading-relaxed">
              {renderTextWithAnalysis()}
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            💡 Renklerin üzerine gelin detayları görün • 🎵 Kelimelere tıklayın ses dosyasında o bölüme gidin
          </p>
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
              Kelime Olayları ({exportData?.events?.length || wordEvents.length})
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
              Duraksama Olayları ({exportData?.pauses?.length || pauseEvents.length})
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'summary' && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="text-center">
                  <p className="text-2xl font-bold text-blue-600">
                    {exportData?.summary?.wer?.toFixed(3) || '—'}
                  </p>
                  <p className="text-sm text-gray-600">WER</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-600">
                    {exportData?.summary?.accuracy?.toFixed(1) || '—'}%
                  </p>
                  <p className="text-sm text-gray-600">Doğruluk</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-purple-600">
                    {exportData?.summary?.wpm?.toFixed(1) || '—'}
                  </p>
                  <p className="text-sm text-gray-600">WPM</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-orange-600">
                    {exportData?.summary?.long_pauses?.count || 0}
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
                              <p className="text-lg font-semibold text-orange-600">{breakdown.substitution}</p>
                              <p className="text-xs text-gray-600">Kelimede Farklılık</p>
                            </div>
                            <div className="text-center">
                              <p className="text-lg font-semibold text-purple-600">{breakdown.repetition}</p>
                              <p className="text-xs text-gray-600">Tekrarlama</p>
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
              ) : (exportData?.events?.length || wordEvents.length) === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-500">Kelime olayı bulunamadı</div>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {(exportData?.events || wordEvents).map((event, index) => (
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
              ) : (exportData?.pauses?.length || pauseEvents.length) === 0 ? (
                <div className="text-center py-8">
                  <div className="text-gray-500">Duraksama olayı bulunamadı</div>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {(exportData?.pauses || pauseEvents).map((event, index) => (
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
      
    </div>
  );
}
