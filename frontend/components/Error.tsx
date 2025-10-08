'use client';

import React from 'react';
import classNames from 'classnames';

interface ErrorProps {
  title?: string;
  message: string;
  type?: 'error' | 'warning' | 'info';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
  onRetry?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export default function Error({ 
  title,
  message, 
  type = 'error',
  size = 'md',
  showIcon = true,
  onRetry,
  onDismiss,
  className 
}: ErrorProps) {
  const typeStyles = {
    error: {
      container: 'bg-red-50 border-red-200 text-red-800',
      icon: 'text-red-400',
      title: 'text-red-800',
      message: 'text-red-700'
    },
    warning: {
      container: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      icon: 'text-yellow-400',
      title: 'text-yellow-800',
      message: 'text-yellow-700'
    },
    info: {
      container: 'bg-blue-50 border-blue-200 text-blue-800',
      icon: 'text-blue-400',
      title: 'text-blue-800',
      message: 'text-blue-700'
    }
  };

  const sizeStyles = {
    sm: 'p-3 text-sm',
    md: 'p-4 text-base',
    lg: 'p-6 text-lg'
  };

  const iconMap = {
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  const styles = typeStyles[type];

  return (
    <div className={classNames(
      'rounded-lg border',
      styles.container,
      sizeStyles[size],
      className
    )}>
      <div className="flex">
        {showIcon && (
          <div className="flex-shrink-0">
            <span className={classNames('text-2xl', styles.icon)}>
              {iconMap[type]}
            </span>
          </div>
        )}
        <div className="ml-3 flex-1">
          {title && (
            <h3 className={classNames('font-medium', styles.title)}>
              {title}
            </h3>
          )}
          <div className={classNames('mt-1', styles.message)}>
            {message}
          </div>
          {(onRetry || onDismiss) && (
            <div className="mt-3 flex space-x-3">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className={classNames(
                    'text-sm font-medium underline hover:no-underline',
                    styles.message
                  )}
                >
                  Tekrar Dene
                </button>
              )}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className={classNames(
                    'text-sm font-medium underline hover:no-underline',
                    styles.message
                  )}
                >
                  Kapat
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Specific Error Components
export function NetworkError({ onRetry, onDismiss }: { onRetry?: () => void; onDismiss?: () => void }) {
  return (
    <Error
      title="Bağlantı Hatası"
      message="Sunucuya bağlanırken bir hata oluştu. Lütfen internet bağlantınızı kontrol edin ve tekrar deneyin."
      type="error"
      onRetry={onRetry}
      onDismiss={onDismiss}
    />
  );
}

export function ValidationError({ message, onDismiss }: { message: string; onDismiss?: () => void }) {
  return (
    <Error
      title="Doğrulama Hatası"
      message={message}
      type="warning"
      onDismiss={onDismiss}
    />
  );
}

export function ServerError({ onRetry, onDismiss }: { onRetry?: () => void; onDismiss?: () => void }) {
  return (
    <Error
      title="Sunucu Hatası"
      message="Sunucuda bir hata oluştu. Lütfen daha sonra tekrar deneyin veya sistem yöneticisi ile iletişime geçin."
      type="error"
      onRetry={onRetry}
      onDismiss={onDismiss}
    />
  );
}

export function NotFoundError({ resource, onRetry, onDismiss }: { 
  resource: string; 
  onRetry?: () => void; 
  onDismiss?: () => void 
}) {
  return (
    <Error
      title="Bulunamadı"
      message={`${resource} bulunamadı. Lütfen arama kriterlerinizi kontrol edin.`}
      type="info"
      onRetry={onRetry}
      onDismiss={onDismiss}
    />
  );
}

export function PermissionError({ onDismiss }: { onDismiss?: () => void }) {
  return (
    <Error
      title="Yetki Hatası"
      message="Bu işlemi gerçekleştirmek için yeterli yetkiniz bulunmuyor. Lütfen sistem yöneticisi ile iletişime geçin."
      type="warning"
      onDismiss={onDismiss}
    />
  );
}

// Toast Error Component
export function ErrorToast({ 
  message, 
  onDismiss 
}: { 
  message: string; 
  onDismiss: () => void 
}) {
  return (
    <div className="fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in">
      <div className="flex items-center">
        <div className="text-2xl mr-2">❌</div>
        <div className="flex-1">
          <div className="font-medium">Hata!</div>
          <div className="text-sm">{message}</div>
        </div>
        <button
          onClick={onDismiss}
          className="ml-4 text-white hover:text-gray-200"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// Success Toast Component
export function SuccessToast({ 
  message, 
  onDismiss 
}: { 
  message: string; 
  onDismiss: () => void 
}) {
  return (
    <div className="fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-slide-in">
      <div className="flex items-center">
        <div className="text-2xl mr-2">✅</div>
        <div className="flex-1">
          <div className="font-medium">Başarılı!</div>
          <div className="text-sm">{message}</div>
        </div>
        <button
          onClick={onDismiss}
          className="ml-4 text-white hover:text-gray-200"
        >
          ✕
        </button>
      </div>
    </div>
  );
}








