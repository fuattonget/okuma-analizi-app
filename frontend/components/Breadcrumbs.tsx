'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRightIcon, HomeIcon } from '@/components/Icon';
import classNames from 'classnames';

interface BreadcrumbItem {
  label: string;
  href?: string;
  icon?: React.ReactNode;
}

interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
  className?: string;
}

export default function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  const pathname = usePathname();

  // Auto-generate breadcrumbs from pathname if not provided
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    if (items) return items;

    const pathSegments = pathname.split('/').filter(Boolean);
    const breadcrumbs: BreadcrumbItem[] = [
      { label: 'Ana Sayfa', href: '/', icon: <HomeIcon size="sm" /> }
    ];

    let currentPath = '';
    pathSegments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      
      // Skip dynamic segments like [id]
      if (segment.startsWith('[') && segment.endsWith(']')) {
        return;
      }

      let label = segment;
      let icon: React.ReactNode | undefined;

      // Map segments to Turkish labels
      switch (segment) {
        case 'students':
          label = 'Öğrenciler';
          icon = <HomeIcon size="sm" />; // You can add a StudentsIcon later
          break;
        case 'analyses':
          label = 'Analizler';
          icon = <HomeIcon size="sm" />; // You can add an AnalysesIcon later
          break;
        case 'texts':
          label = 'Metinler';
          icon = <HomeIcon size="sm" />; // You can add a TextsIcon later
          break;
        case 'login':
          label = 'Giriş';
          break;
        default:
          // If it's a dynamic ID, try to get a meaningful label
          if (segment.match(/^[a-f0-9]{24}$/)) {
            // This looks like a MongoDB ObjectId
            label = 'Detay';
          } else {
            // Capitalize first letter
            label = segment.charAt(0).toUpperCase() + segment.slice(1);
          }
      }

      // Don't add href for the last item (current page)
      const href = index === pathSegments.length - 1 ? undefined : currentPath;

      breadcrumbs.push({
        label,
        href,
        icon
      });
    });

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  if (breadcrumbs.length <= 1) {
    return null; // Don't show breadcrumbs if we're only on the home page
  }

  return (
    <nav 
      className={classNames(
        'flex items-center space-x-1 text-sm text-gray-500 dark:text-slate-400',
        className
      )}
      aria-label="Breadcrumb"
    >
      {breadcrumbs.map((item, index) => (
        <React.Fragment key={index}>
          {index > 0 && (
            <ChevronRightIcon 
              size="sm" 
              className="text-gray-400 dark:text-slate-500 mx-1" 
            />
          )}
          {item.href ? (
            <Link
              href={item.href}
              className="flex items-center space-x-1 hover:text-gray-700 dark:hover:text-slate-200 transition-colors"
            >
              {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
              <span>{item.label}</span>
            </Link>
          ) : (
            <span className="flex items-center space-x-1 text-gray-900 dark:text-slate-100 font-medium">
              {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
              <span>{item.label}</span>
            </span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}







