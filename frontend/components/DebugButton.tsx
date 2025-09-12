'use client';

import { useDebugStore } from '@/lib/debug-store';

const DebugButton = () => {
  const { visible, toggle } = useDebugStore();
  
  // Only show if DEBUG mode is enabled
  if (process.env.NEXT_PUBLIC_DEBUG !== '1') {
    return null;
  }

  return (
    <button
      onClick={toggle}
      className={`fixed top-4 right-4 z-40 px-3 py-2 rounded-full text-sm font-medium transition-all ${
        visible 
          ? 'bg-red-600 hover:bg-red-700 text-white' 
          : 'bg-blue-600 hover:bg-blue-700 text-white'
      }`}
      title="Debug Panel (Ctrl+D)"
    >
      {visible ? 'Hide Debug' : 'Debug'}
    </button>
  );
};

export default DebugButton;


