'use client';

import { useState, useRef, useEffect } from 'react';
import { AudioIcon } from '@/components/Icon';
import classNames from 'classnames';

interface AudioRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  onError: (error: string) => void;
  disabled?: boolean;
  className?: string;
}

export default function AudioRecorder({ 
  onRecordingComplete, 
  onError, 
  disabled = false,
  className = ''
}: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const MAX_RECORDING_TIME = 5 * 60 * 1000; // 5 dakika

  // Mikrofon izni kontrolü
  useEffect(() => {
    checkMicrophonePermission();
  }, []);

  const checkMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      setHasPermission(true);
    } catch (error) {
      setHasPermission(false);
      onError('Mikrofon erişimi reddedildi. Lütfen tarayıcı ayarlarından mikrofon iznini verin.');
    }
  };

  const startRecording = async () => {
    try {
      if (hasPermission === false) {
        onError('Mikrofon erişimi gerekli. Lütfen tarayıcı ayarlarından mikrofon iznini verin.');
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        }
      });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setRecordedAudio(audioBlob);
        setAudioUrl(URL.createObjectURL(audioBlob));
        onRecordingComplete(audioBlob);
        
        // Stream'i temizle
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setIsPaused(false);
      setRecordingTime(0);

      // Timer başlat
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 100;
          if (newTime >= MAX_RECORDING_TIME) {
            stopRecording();
            onError('Maksimum kayıt süresi (5 dakika) aşıldı.');
          }
          return newTime;
        });
      }, 100);

    } catch (error) {
      console.error('Kayıt başlatma hatası:', error);
      onError('Kayıt başlatılamadı. Mikrofon erişimini kontrol edin.');
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording && !isPaused) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && isRecording && isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      
      // Timer'ı yeniden başlat
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 100;
          if (newTime >= MAX_RECORDING_TIME) {
            stopRecording();
            onError('Maksimum kayıt süresi (5 dakika) aşıldı.');
          }
          return newTime;
        });
      }, 100);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const deleteRecording = () => {
    setRecordedAudio(null);
    setAudioUrl(null);
    setRecordingTime(0);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
  };

  const playRecording = () => {
    if (audioRef.current && audioUrl) {
      audioRef.current.play();
    }
  };

  const formatTime = (ms: number) => {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  };

  const getRecordingStatus = () => {
    if (isRecording && !isPaused) return 'Kaydediliyor...';
    if (isRecording && isPaused) return 'Duraklatıldı';
    if (recordedAudio) return 'Kayıt tamamlandı';
    return 'Kayıt hazır';
  };

  const getStatusColor = () => {
    if (isRecording && !isPaused) return 'text-red-600';
    if (isRecording && isPaused) return 'text-yellow-600';
    if (recordedAudio) return 'text-green-600';
    return 'text-gray-600';
  };

  // Cleanup
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [audioUrl]);

  if (hasPermission === false) {
    return (
      <div className={classNames('border-2 border-dashed border-red-300 rounded-lg p-6 text-center', className)}>
        <div className="text-red-600 mb-2">
          <AudioIcon size="lg" />
        </div>
        <div className="text-sm font-medium text-red-600 mb-2">
          Mikrofon Erişimi Gerekli
        </div>
        <div className="text-xs text-red-500 mb-4">
          Tarayıcı ayarlarından mikrofon iznini verin
        </div>
        <button
          onClick={checkMicrophonePermission}
          className="px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
        >
          Tekrar Dene
        </button>
      </div>
    );
  }

  return (
    <div className={classNames('border-2 border-dashed border-gray-300 dark:border-slate-600 rounded-lg p-4', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <AudioIcon size="sm" className="text-gray-600 dark:text-slate-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
            🎤 Ses Kaydet
          </span>
        </div>
        <div className={classNames('text-xs font-medium', getStatusColor())}>
          {getRecordingStatus()}
        </div>
      </div>

      {/* Recording Controls */}
      <div className="space-y-3">
        {/* Time Display */}
        <div className="text-center">
          <div className="text-2xl font-mono text-gray-800 dark:text-slate-200">
            {formatTime(recordingTime)}
          </div>
          <div className="text-xs text-gray-500 dark:text-slate-400">
            Maksimum: 05:00
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex justify-center space-x-2">
          {!isRecording && !recordedAudio && (
            <button
              onClick={startRecording}
              disabled={disabled}
              className="px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
            >
              <span>🔴</span>
              <span>Kaydet</span>
            </button>
          )}

          {isRecording && !isPaused && (
            <>
              <button
                onClick={pauseRecording}
                disabled={disabled}
                className="px-4 py-2 bg-yellow-600 text-white text-sm rounded hover:bg-yellow-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
              >
                <span>⏸️</span>
                <span>Durdur</span>
              </button>
              <button
                onClick={stopRecording}
                disabled={disabled}
                className="px-4 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
              >
                <span>⏹️</span>
                <span>Bitir</span>
              </button>
            </>
          )}

          {isRecording && isPaused && (
            <>
              <button
                onClick={resumeRecording}
                disabled={disabled}
                className="px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
              >
                <span>▶️</span>
                <span>Devam</span>
              </button>
              <button
                onClick={stopRecording}
                disabled={disabled}
                className="px-4 py-2 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
              >
                <span>⏹️</span>
                <span>Bitir</span>
              </button>
            </>
          )}

          {recordedAudio && (
            <>
              <button
                onClick={playRecording}
                disabled={disabled}
                className="px-4 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
              >
                <span>▶️</span>
                <span>Dinle</span>
              </button>
              <button
                onClick={deleteRecording}
                disabled={disabled}
                className="px-4 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center space-x-1"
              >
                <span>🗑️</span>
                <span>Sil</span>
              </button>
            </>
          )}
        </div>

        {/* Audio Player */}
        {audioUrl && (
          <div className="mt-3">
            <audio
              ref={audioRef}
              src={audioUrl}
              controls
              className="w-full"
              preload="metadata"
            >
              Tarayıcınız ses dosyasını desteklemiyor.
            </audio>
          </div>
        )}

        {/* File Info */}
        {recordedAudio && (
          <div className="text-center text-xs text-gray-500 dark:text-slate-400">
            <div>Dosya boyutu: {(recordedAudio.size / 1024 / 1024).toFixed(2)} MB</div>
            <div>Format: WebM</div>
          </div>
        )}
      </div>
    </div>
  );
}
