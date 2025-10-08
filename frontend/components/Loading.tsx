'use client';

import React from 'react';
import classNames from 'classnames';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'dots' | 'pulse' | 'skeleton';
  text?: string;
  className?: string;
  fullScreen?: boolean;
}

export default function Loading({ 
  size = 'md', 
  variant = 'spinner', 
  text, 
  className,
  fullScreen = false 
}: LoadingProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  const renderLoading = () => {
    switch (variant) {
      case 'spinner':
        return (
          <div className={classNames(
            'loading-spinner',
            sizeClasses[size],
            className
          )} />
        );
      
      case 'dots':
        return (
          <div className={classNames('loading-dots', className)}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        );
      
      case 'pulse':
        return (
          <div className={classNames(
            'animate-pulse',
            'bg-blue-500 rounded-full',
            sizeClasses[size],
            className
          )} />
        );
      
      case 'skeleton':
        return (
          <div className={classNames('skeleton', sizeClasses[size], className)} />
        );
      
      default:
        return (
          <div className={classNames(
            'loading-spinner',
            sizeClasses[size],
            className
          )} />
        );
    }
  };

  const content = (
    <div className={classNames(
      'flex flex-col items-center justify-center space-y-3',
      textSizeClasses[size]
    )}>
      {renderLoading()}
      {text && (
        <p className="text-gray-600 font-medium animate-pulse">
          {text}
        </p>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        {content}
      </div>
    );
  }

  return content;
}

// Skeleton Loading Components
export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton-avatar mb-4"></div>
      <div className="space-y-2">
        <div className="skeleton-text w-3/4"></div>
        <div className="skeleton-text w-1/2"></div>
        <div className="skeleton-text w-5/6"></div>
      </div>
    </div>
  );
}

export function SkeletonList({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton-card">
          <div className="flex items-center space-x-4">
            <div className="skeleton-avatar"></div>
            <div className="flex-1 space-y-2">
              <div className="skeleton-text w-1/3"></div>
              <div className="skeleton-text w-1/4"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonTable({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex space-x-4">
          {Array.from({ length: columns }).map((_, i) => (
            <div key={i} className="skeleton-text w-20"></div>
          ))}
        </div>
      </div>
      <div className="divide-y divide-gray-200">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="px-6 py-4">
            <div className="flex space-x-4">
              {Array.from({ length: columns }).map((_, j) => (
                <div key={j} className="skeleton-text w-16"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}








