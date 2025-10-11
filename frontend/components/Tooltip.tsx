'use client';

import React, { useState, useRef, useEffect } from 'react';
import classNames from 'classnames';

interface TooltipProps {
  content: string | React.ReactNode;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
  disabled?: boolean;
  className?: string;
  maxWidth?: string;
}

export default function Tooltip({
  content,
  children,
  position = 'top',
  delay = 300,
  disabled = false,
  className,
  maxWidth = '200px'
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [actualPosition, setActualPosition] = useState(position);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLDivElement>(null);

  const showTooltip = () => {
    if (disabled) return;
    
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
    }, delay);
  };

  const hideTooltip = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  // Auto-adjust position based on viewport
  useEffect(() => {
    if (isVisible && tooltipRef.current && triggerRef.current) {
      const tooltip = tooltipRef.current;
      const trigger = triggerRef.current;
      const rect = trigger.getBoundingClientRect();
      const tooltipRect = tooltip.getBoundingClientRect();
      
      let newPosition = position;
      
      // Check if tooltip would go off screen
      if (position === 'top' && rect.top - tooltipRect.height < 0) {
        newPosition = 'bottom';
      } else if (position === 'bottom' && rect.bottom + tooltipRect.height > window.innerHeight) {
        newPosition = 'top';
      } else if (position === 'left' && rect.left - tooltipRect.width < 0) {
        newPosition = 'right';
      } else if (position === 'right' && rect.right + tooltipRect.width > window.innerWidth) {
        newPosition = 'left';
      }
      
      setActualPosition(newPosition);
    }
  }, [isVisible, position]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const getPositionClasses = () => {
    switch (actualPosition) {
      case 'top':
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
      case 'bottom':
        return 'top-full left-1/2 transform -translate-x-1/2 mt-2';
      case 'left':
        return 'right-full top-1/2 transform -translate-y-1/2 mr-2';
      case 'right':
        return 'left-full top-1/2 transform -translate-y-1/2 ml-2';
      default:
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
    }
  };

  const getArrowClasses = () => {
    switch (actualPosition) {
      case 'top':
        return 'top-full left-1/2 transform -translate-x-1/2 border-t-gray-900 dark:border-t-gray-700';
      case 'bottom':
        return 'bottom-full left-1/2 transform -translate-x-1/2 border-b-gray-900 dark:border-b-gray-700';
      case 'left':
        return 'left-full top-1/2 transform -translate-y-1/2 border-l-gray-900 dark:border-l-gray-700';
      case 'right':
        return 'right-full top-1/2 transform -translate-y-1/2 border-r-gray-900 dark:border-r-gray-700';
      default:
        return 'top-full left-1/2 transform -translate-x-1/2 border-t-gray-900 dark:border-t-gray-700';
    }
  };

  if (disabled || !content) {
    return <>{children}</>;
  }

  return (
    <div
      ref={triggerRef}
      className="relative inline-block"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className={classNames(
            'absolute z-50 px-3 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg shadow-lg transition-opacity duration-200 dark:bg-gray-700',
            getPositionClasses(),
            className
          )}
          style={{ maxWidth }}
          role="tooltip"
        >
          <div
            className={classNames(
              'absolute w-0 h-0 border-4 border-transparent',
              getArrowClasses()
            )}
          />
          {content}
        </div>
      )}
    </div>
  );
}

// Predefined tooltip variants for common use cases
export function InfoTooltip({ content, children, ...props }: Omit<TooltipProps, 'position'>) {
  return (
    <Tooltip content={content} position="top" {...props}>
      {children}
    </Tooltip>
  );
}

export function HelpTooltip({ content, children, ...props }: Omit<TooltipProps, 'position'>) {
  return (
    <Tooltip content={content} position="right" {...props}>
      {children}
    </Tooltip>
  );
}

export function ActionTooltip({ content, children, ...props }: Omit<TooltipProps, 'position'>) {
  return (
    <Tooltip content={content} position="bottom" {...props}>
      {children}
    </Tooltip>
  );
}










