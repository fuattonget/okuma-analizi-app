'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, Text, AnalysisSummary } from '@/lib/api';
import { useAnalysisStore } from '@/lib/store';
import classNames from 'classnames';
import DebugButton from '@/components/DebugButton';
import DebugPanel from '@/components/DebugPanel';

export default function HomePage() {
  const router = useRouter();
  const { analyses, setAnalyses, addAnalysis, updateAnalysis, startPolling, stopPolling } = useAnalysisStore();
  
  const [texts, setTexts] = useState<Text[]>([]);
  const [filteredTexts, setFilteredTexts] = useState<Text[]>([]);
  const [selectedTextId, setSelectedTextId] = useState<string>('');
  const [customText, setCustomText] = useState('');
  const [grade, setGrade] = useState<number | ''>('');
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);

  // Load texts and analyses on mount
  useEffect(() => {
    loadTexts();
    loadAnalyses();
  }, []);

  // Filter texts by grade
  useEffect(() => {
    if (grade) {
      const filtered = texts.filter(t => t.grade === grade);
      setFilteredTexts(filtered);
    } else {
      setFilteredTexts(texts);
    }
  }, [grade, texts]);

  // Update customText when a text is selected
  useEffect(() => {
    console.log('useEffect triggered:', { selectedTextId, textsLength: texts.length });
    if (selectedTextId && texts.length > 0) {
      const selectedText = texts.find(t => t.id === selectedTextId);
      console.log('Selected text found:', selectedText);
      if (selectedText) {
        console.log('Setting customText to:', selectedText.body);
        setCustomText(selectedText.body);
        setGrade(selectedText.grade);
      }
    }
  }, [selectedTextId, texts]);

  const loadTexts = async () => {
    try {
      const textsData = await apiClient.getTexts();
      console.log('Loaded texts:', textsData);
      setTexts(textsData);
    } catch (error) {
      console.error('Failed to load texts:', error);
    }
  };

  const loadAnalyses = async () => {
    try {
      const analysesData = await apiClient.getAnalyses(20);
      setAnalyses(analysesData);
    } catch (error) {
      console.error('Failed to load analyses:', error);
    }
  };

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
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };


  const startAnalysis = async () => {
    if (!selectedFile || !customText.trim()) return;
    
    setIsUploading(true);
    try {
      // Create a temporary text if using custom text
      let textId = selectedTextId;
      if (!selectedTextId && customText.trim()) {
        const tempText = await apiClient.createText({
          title: `Geçici Metin - ${new Date().toLocaleString('tr-TR')}`,
          grade: grade as number,
          body: customText.trim(),
        });
        textId = tempText.text_id; // Use text_id for upload
        // Add to local texts list
        setTexts([tempText, ...texts]);
      } else if (selectedTextId) {
        // Find the selected text and use its text_id
        const selectedText = texts.find(t => t.id === selectedTextId);
        if (selectedText) {
          textId = selectedText.text_id;
        }
      }
      
      const response = await apiClient.uploadAudio(selectedFile, textId);
      
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
          const status = await apiClient.getAnalysisStatus(response.analysis_id);
          updateAnalysis(response.analysis_id, { status: status.status });
          
          if (status.status === 'done' || status.status === 'failed') {
            // Reload full analysis data
            const fullAnalysis = await apiClient.getAnalysis(response.analysis_id);
            updateAnalysis(response.analysis_id, fullAnalysis);
            stopPolling(response.analysis_id);
          }
        } catch (error) {
          console.error('Failed to poll analysis status:', error);
          stopPolling(response.analysis_id);
        }
      });
      
      // Reset form
      setSelectedFile(null);
      setSelectedTextId('');
      setCustomText('');
      setGrade('');
      
      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 5000);
      
    } catch (error) {
      console.error('Failed to start analysis:', error);
      alert('Analiz başlatılırken hata oluştu. Lütfen tekrar deneyin.');
    } finally {
      setIsUploading(false);
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

  return (
    <div className="space-y-8">
      {/* Upload Section */}
      <div className="card max-w-4xl mx-auto">
        <h2 className="text-2xl font-semibold mb-8 text-center">Ses Dosyası Analizi</h2>
        
        <div className="space-y-8">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-4">
              Ses Dosyası
            </label>
            <div
              className={classNames(
                'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
                dragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300',
                selectedFile ? 'border-green-400 bg-green-50' : ''
              )}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <input
                id="file-input"
                type="file"
                accept="audio/*"
                onChange={handleFileSelect}
                className="hidden"
              />
              {selectedFile ? (
                <div>
                  <div className="text-green-600 text-4xl mb-2">🎵</div>
                  <p className="text-green-600 font-medium text-lg">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">Dosya seçildi - Analiz için hazır</p>
                </div>
              ) : (
                <div>
                  <div className="text-gray-400 text-4xl mb-2">📁</div>
                  <p className="text-gray-600 text-lg">Dosyayı buraya sürükleyin veya tıklayın</p>
                  <p className="text-sm text-gray-500">MP3, WAV, M4A desteklenir</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Text Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sınıf Seviyesi
              </label>
              <select
                value={grade}
                onChange={(e) => {
                  setGrade(e.target.value ? parseInt(e.target.value) : '');
                  setSelectedTextId(''); // Reset selection when grade changes
                }}
                className="select text-lg py-3"
              >
                <option value="">Sınıf seçiniz</option>
                <option value="1">1. Sınıf</option>
                <option value="2">2. Sınıf</option>
                <option value="3">3. Sınıf</option>
                <option value="4">4. Sınıf</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Örnek Metin Seç
              </label>
              <select
                value={selectedTextId}
                onChange={(e) => setSelectedTextId(e.target.value)}
                className="select text-lg py-3"
                disabled={!grade}
              >
                <option value="">{grade ? 'Metin seçiniz' : 'Önce sınıf seçiniz'}</option>
                {filteredTexts.map((text) => (
                  <option key={text.id} value={text.id}>
                    {text.title}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          {/* Target Text Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Hedef Metin
            </label>
            <textarea
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              placeholder="Analiz edilecek metni buraya yazın veya yukarıdan seçin..."
              className="textarea h-32 text-lg"
            />
            <p className="text-sm text-gray-500 mt-1">
              Metin seçtiyseniz otomatik doldurulur, isterseniz düzenleyebilirsiniz.
            </p>
          </div>
          
          {/* Analyze Button */}
          <div className="text-center">
            <button
              onClick={startAnalysis}
              disabled={!selectedFile || !customText.trim() || isUploading}
              className={classNames(
                'btn text-lg px-8 py-4',
                (!selectedFile || !customText.trim() || isUploading) 
                  ? 'btn-secondary' 
                  : 'btn-primary'
              )}
            >
              {isUploading ? (
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Analiz Ediliyor...
                </div>
              ) : (
                'Analiz Et'
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Success Message */}
      {showSuccess && (
        <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50">
          <div className="flex items-center">
            <div className="text-2xl mr-2">✅</div>
            <div>
              <div className="font-medium">Analiz Başlatıldı!</div>
              <div className="text-sm">Geçmiş Analizler sayfasından takip edebilirsiniz.</div>
            </div>
          </div>
        </div>
      )}
      
      {/* Debug Components */}
      <DebugButton />
      <DebugPanel />
    </div>
  );
}
