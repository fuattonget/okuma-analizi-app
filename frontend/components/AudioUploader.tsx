'use client';

import { useState, useRef } from 'react';
import { AudioIcon } from '@/components/Icon';
import classNames from 'classnames';

interface AudioUploaderProps {
  onFileSelect: (file: File) => void;
  onError: (error: string) => void;
  selectedFile: File | null;
  disabled?: boolean;
  className?: string;
}

export default function AudioUploader({ 
  onFileSelect, 
  onError, 
  selectedFile,
  disabled = false,
  className = ''
}: AudioUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    // Dosya boyutu kontrolü (50MB)
    if (file.size > 50 * 1024 * 1024) {
      return 'Dosya boyutu 50MB\'dan büyük olamaz';
    }

    // Dosya türü kontrolü
    const allowedTypes = [
      'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/m4a', 'audio/x-m4a',
      'audio/aac', 'audio/ogg', 'audio/flac', 'audio/webm'
    ];
    
    if (!allowedTypes.includes(file.type)) {
      return 'Desteklenmeyen dosya türü. MP3, WAV, M4A, AAC, OGG, FLAC, WebM dosyaları kabul edilir.';
    }

    return null;
  };

  const handleFileSelect = (file: File) => {
    const error = validateFile(file);
    if (error) {
      onError(error);
      return;
    }
    
    onFileSelect(file);
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

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      handleFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={classNames('border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-lg p-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <AudioIcon size="sm" className="text-gray-600 dark:text-slate-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
            📁 Dosya Yükle
          </span>
        </div>
        {selectedFile && (
          <div className="text-xs text-green-600 font-medium">
            Dosya seçildi
          </div>
        )}
      </div>

      {/* Upload Area */}
      <div
        className={classNames(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          dragActive ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-slate-600',
          selectedFile ? 'border-green-400 bg-green-50 dark:bg-green-900/20' : '',
          disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-gray-400 dark:hover:border-slate-500'
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="audio/*,.mp3,.wav,.m4a,.aac,.ogg,.flac,.webm"
          onChange={handleFileInputChange}
          className="hidden"
          disabled={disabled}
        />

        <div className="space-y-2">
          {selectedFile ? (
            <div className="text-green-600">
              <div className="mb-2">
                <AudioIcon size="lg" className="text-gray-400" />
              </div>
              <div className="font-medium text-gray-900 dark:text-slate-100">
                {selectedFile.name}
              </div>
              <div className="text-sm text-gray-500 dark:text-slate-400">
                {formatFileSize(selectedFile.size)}
              </div>
              <div className="text-xs text-gray-400 dark:text-slate-500 mt-1">
                {selectedFile.type}
              </div>
            </div>
          ) : (
            <div className="text-gray-500 dark:text-slate-400">
              <div className="mb-2">
                <AudioIcon size="lg" className="text-gray-400 dark:text-slate-500" />
              </div>
              <div className="text-base sm:text-lg font-medium text-gray-900 dark:text-slate-100">
                Ses dosyasını buraya sürükleyin veya tıklayın
              </div>
              <div className="text-xs sm:text-sm text-gray-500 dark:text-slate-400">
                MP3, WAV, M4A, AAC, OGG, FLAC, WebM formatları desteklenir
              </div>
              <div className="text-xs text-blue-600 dark:text-blue-400 mt-2">🤙</div>
            </div>
          )}
        </div>
      </div>

      {/* File Actions */}
      {selectedFile && (
        <div className="mt-3 flex justify-center">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Farklı Dosya Seç
          </button>
        </div>
      )}
    </div>
  );
}
