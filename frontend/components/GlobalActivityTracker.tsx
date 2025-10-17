'use client';

import { useEffect } from 'react';

/**
 * Global Activity Tracker Component
 * 
 * This component tracks user activity (mouse, keyboard, touch, scroll) across the entire app
 * and updates the last_activity timestamp in localStorage. This ensures that the inactivity
 * timeout works correctly even when users switch between pages or tabs.
 * 
 * Key features:
 * - Tracks multiple activity events (mousedown, keydown, scroll, touchstart, click)
 * - Updates localStorage last_activity timestamp on any activity
 * - Prevents duplicate updates (debounced to 1 second)
 * - Cleans up event listeners on unmount
 */
export default function GlobalActivityTracker() {
  useEffect(() => {
    // Only run in browser environment
    if (typeof window === 'undefined') {
      return;
    }

    let lastUpdateTime = 0;
    const UPDATE_THROTTLE = 1000; // Update at most once per second

    const handleActivity = () => {
      const now = Date.now();
      
      // Throttle updates to avoid excessive localStorage writes
      if (now - lastUpdateTime < UPDATE_THROTTLE) {
        return;
      }
      
      lastUpdateTime = now;
      localStorage.setItem('last_activity', now.toString());
    };

    // Activity events to track
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    
    // Add event listeners
    activityEvents.forEach(event => {
      document.addEventListener(event, handleActivity, { passive: true });
    });

    // Cleanup on unmount
    return () => {
      activityEvents.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });
    };
  }, []);

  // This component doesn't render anything
  return null;
}

