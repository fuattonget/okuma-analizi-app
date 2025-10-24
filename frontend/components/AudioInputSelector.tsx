'use client';

import { useState } from 'react';
import { AudioIcon } from '@/components/Icon';
import AudioRecorder from './AudioRecorder';
import AudioUploader from './AudioUploader';
import classNames from 'classnames';

interface AudioInputSelectorProps {
  onFileSelect: (file: File) => void;
  onError: (error: string) => void;
  selectedFile: File | null;
  disabled?: boolean;
  className?: string;
}

export default function AudioInputSelector({ 
  onFileSelect, 
  onError, 
  selectedFile,
  disabled = false,
  className = ''
}: AudioInputSelectorProps) {
  const [inputType, setInputType] = useState<'record' | 'upload'>('upload');

  const handleRecordingComplete = (audioBlob: Blob) => {
    // WebM blob'u File objesine dönüştür
    const file = new File([audioBlob], `recording-${Date.now()}.webm`, {
      type: 'audio/webm'
    });
    onFileSelect(file);
  };

  const handleFileSelect = (file: File) => {
    onFileSelect(file);
  };

  const handleError = (error: string) => {
    onError(error);
  };

  return (
    <div className={classNames('space-y-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700 dark:text-slate-300">
          <AudioIcon size="sm" className="mr-2" />
          Ses Dosyası <span className="text-red-500">*</span>
        </label>
        {selectedFile && (
          <div className="text-xs text-green-600 font-medium">
            ✓ Dosya seçildi
          </div>
        )}
      </div>

      {/* Input Type Selector */}
      <div className="flex space-x-2 mb-4">
        <button
          type="button"
          onClick={() => setInputType('upload')}
          disabled={disabled}
          className={classNames(
            'flex-1 px-4 py-2 text-sm font-medium rounded-md border transition-colors',
            inputType === 'upload'
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600 dark:hover:bg-slate-700',
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          )}
        >
          📁 Dosya Yükle
        </button>
        <button
          type="button"
          onClick={() => setInputType('record')}
          disabled={disabled}
          className={classNames(
            'flex-1 px-4 py-2 text-sm font-medium rounded-md border transition-colors',
            inputType === 'record'
              ? 'bg-blue-600 text-white border-blue-600'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-600 dark:hover:bg-slate-700',
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          )}
        >
          🎤 Ses Kaydet
        </button>
      </div>

      {/* Input Components */}
      <div className="min-h-[200px]">
        {inputType === 'upload' ? (
          <AudioUploader
            onFileSelect={handleFileSelect}
            onError={handleError}
            selectedFile={selectedFile}
            disabled={disabled}
          />
        ) : (
          <AudioRecorder
            onRecordingComplete={handleRecordingComplete}
            onError={handleError}
            disabled={disabled}
          />
        )}
      </div>

      {/* File Info */}
      {selectedFile && (
        <div className="bg-gray-50 dark:bg-slate-700 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AudioIcon size="sm" className="text-gray-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
                {selectedFile.name}
              </span>
            </div>
            <div className="text-xs text-gray-500 dark:text-slate-400">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </div>
          </div>
          <div className="text-xs text-gray-500 dark:text-slate-400 mt-1">
            {selectedFile.type}
          </div>
        </div>
      )}
    </div>
  );
}
