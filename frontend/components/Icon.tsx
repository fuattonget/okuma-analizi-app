'use client';

import React from 'react';
import classNames from 'classnames';

interface IconProps {
  name: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  color?: string;
}

// SVG Icon Components
const HomeIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
  </svg>
);

const AnalysesIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const TextsIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const StudentsIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
  </svg>
);

const MenuIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
  </svg>
);

const LogoutIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
  </svg>
);

const AddIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
  </svg>
);

const EditIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  </svg>
);

const DeleteIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

const ViewIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const RefreshIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const SearchIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
  </svg>
);

const FilterIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
  </svg>
);

const AudioIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
  </svg>
);

const UserIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
);

const GradeIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l9-5-9-5-9 5 9 5z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l6.16-3.422a12.083 12.083 0 01.665 6.479A11.952 11.952 0 0012 20.055a11.952 11.952 0 00-6.824-2.998 12.078 12.078 0 01.665-6.479L12 14z" />
  </svg>
);

const BookIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const AnalysisIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const TimeIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const DateIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const LoadingIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

// New professional icons inspired by Figma pack
const LockIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
  </svg>
);

const UnlockIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
  </svg>
);

const SettingsIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
);

const DownloadIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
  </svg>
);

const UploadIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
);

const StarIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
  </svg>
);

const HeartIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
  </svg>
);

const CalendarIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const ClockIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const MailIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
  </svg>
);

const PhoneIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
  </svg>
);

const GlobeIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
  </svg>
);

const ShieldIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

const BellIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
  </svg>
);

const EyeIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
);

const EyeOffIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
  </svg>
);

const TargetIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z" />
    <circle cx="12" cy="12" r="2" />
  </svg>
);

const LightbulbIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
  </svg>
);

const MusicIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
  </svg>
);

const PlusIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
);

const ChevronRightIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
  </svg>
);

const InfoIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CheckIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const CrossIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const WarningIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ErrorIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const SuccessIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const ActiveIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const InactiveIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const RunningIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const CompletedIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const FailedIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const QueuedIconSVG = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  // Navigation
  'home': HomeIconSVG,
  'analyses': AnalysesIconSVG,
  'texts': TextsIconSVG,
  'students': StudentsIconSVG,
  'menu': MenuIconSVG,
  'logout': LogoutIconSVG,

  // Actions
  'add': AddIconSVG,
  'edit': EditIconSVG,
  'delete': DeleteIconSVG,
  'view': ViewIconSVG,
  'refresh': RefreshIconSVG,
  'search': SearchIconSVG,
  'filter': FilterIconSVG,

  // File types
  'audio': AudioIconSVG,

  // User interface
  'user': UserIconSVG,
  'grade': GradeIconSVG,
  'book': BookIconSVG,
  'analysis': AnalysisIconSVG,
  'time': TimeIconSVG,
  'date': DateIconSVG,

  // System
  'loading': LoadingIconSVG,
  'check': CheckIconSVG,
  'cross': CrossIconSVG,
  'warning': WarningIconSVG,
  'error': ErrorIconSVG,
  'success': SuccessIconSVG,
  'active': ActiveIconSVG,
  'inactive': InactiveIconSVG,
  'running': RunningIconSVG,
  'completed': CompletedIconSVG,
  'failed': FailedIconSVG,
  'queued': QueuedIconSVG,

  // New professional icons
  'lock': LockIconSVG,
  'unlock': UnlockIconSVG,
  'settings': SettingsIconSVG,
  'download': DownloadIconSVG,
  'upload': UploadIconSVG,
  'star': StarIconSVG,
  'heart': HeartIconSVG,
  'calendar': CalendarIconSVG,
  'clock': ClockIconSVG,
  'mail': MailIconSVG,
  'phone': PhoneIconSVG,
  'globe': GlobeIconSVG,
  'shield': ShieldIconSVG,
  'bell': BellIconSVG,
    'eye': EyeIconSVG,
    'eye-off': EyeOffIconSVG,
    'target': TargetIconSVG,
    'lightbulb': LightbulbIconSVG,
    'music': MusicIconSVG,
    'plus': PlusIconSVG,
    'chevron-right': ChevronRightIconSVG,
    'info': InfoIconSVG,
  };

const sizeClasses = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8'
};

export default function Icon({ 
  name, 
  size = 'md', 
  className,
  color 
}: IconProps) {
  const IconComponent = iconMap[name];
  
  if (!IconComponent) {
    console.warn(`Icon "${name}" not found.`);
    return <span className="text-red-500">❓</span>;
  }

  return (
    <IconComponent 
      className={classNames(
        'inline-block',
        sizeClasses[size],
        className
      )}
      {...(color && { style: { color } })}
    />
  );
}

// Predefined icon components for common use cases
export function HomeIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="home" size={size} className={className} />;
}

export function AnalysesIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="analyses" size={size} className={className} />;
}

export function TextsIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="texts" size={size} className={className} />;
}

export function StudentsIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="students" size={size} className={className} />;
}

export function AddIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="add" size={size} className={className} />;
}

export function EditIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="edit" size={size} className={className} />;
}

export function DeleteIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="delete" size={size} className={className} />;
}

export function ViewIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="view" size={size} className={className} />;
}

export function AudioIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="audio" size={size} className={className} />;
}

export function UserIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="user" size={size} className={className} />;
}

export function GradeIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="grade" size={size} className={className} />;
}

export function BookIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="book" size={size} className={className} />;
}

export function AnalysisIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="analysis" size={size} className={className} />;
}

export function TimeIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="time" size={size} className={className} />;
}

export function DateIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="date" size={size} className={className} />;
}

export function SearchIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="search" size={size} className={className} />;
}

export function FilterIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="filter" size={size} className={className} />;
}

export function RefreshIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="refresh" size={size} className={className} />;
}

export function LogoutIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="logout" size={size} className={className} />;
}

export function MenuIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="menu" size={size} className={className} />;
}

export function CheckIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="check" size={size} className={className} />;
}

export function CrossIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="cross" size={size} className={className} />;
}

export function WarningIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="warning" size={size} className={className} />;
}

export function ErrorIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="error" size={size} className={className} />;
}

export function SuccessIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="success" size={size} className={className} />;
}

// Status icons
export function ActiveIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="active" size={size} className={className} />;
}

export function InactiveIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="inactive" size={size} className={className} />;
}

export function RunningIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="running" size={size} className={className} />;
}

export function CompletedIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="completed" size={size} className={className} />;
}

export function FailedIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="failed" size={size} className={className} />;
}

export function QueuedIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="queued" size={size} className={className} />;
}

// New professional icons
export function LockIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="lock" size={size} className={className} />;
}

export function UnlockIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="unlock" size={size} className={className} />;
}

export function SettingsIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="settings" size={size} className={className} />;
}

export function DownloadIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="download" size={size} className={className} />;
}

export function UploadIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="upload" size={size} className={className} />;
}

export function StarIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="star" size={size} className={className} />;
}

export function HeartIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="heart" size={size} className={className} />;
}

export function CalendarIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="calendar" size={size} className={className} />;
}

export function ClockIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="clock" size={size} className={className} />;
}

export function MailIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="mail" size={size} className={className} />;
}

export function PhoneIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="phone" size={size} className={className} />;
}

export function GlobeIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="globe" size={size} className={className} />;
}

export function ShieldIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="shield" size={size} className={className} />;
}

export function BellIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="bell" size={size} className={className} />;
}

export function EyeIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="eye" size={size} className={className} />;
}

export function EyeOffIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="eye-off" size={size} className={className} />;
}

export function TargetIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="target" size={size} className={className} />;
}

export function LightbulbIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="lightbulb" size={size} className={className} />;
}

export function MusicIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="music" size={size} className={className} />;
}

export function PlusIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="plus" size={size} className={className} />;
}

export function ChevronRightIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="chevron-right" size={size} className={className} />;
}

export function InfoIcon({ size = 'md', className }: { size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'; className?: string }) {
  return <Icon name="info" size={size} className={className} />;
}