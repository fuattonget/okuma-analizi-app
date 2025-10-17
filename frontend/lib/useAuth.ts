import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

const INACTIVITY_TIMEOUT = 3 * 60 * 60 * 1000; // 3 hours in milliseconds
const INACTIVITY_CHECK_INTERVAL = 60 * 1000; // Check every 1 minute

export function useAuth() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [user, setUser] = useState(null);

  const logout = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      localStorage.removeItem('last_activity');
    }
    setIsAuthenticated(false);
    setIsAuthLoading(false);
    setUser(null);
    router.push('/login');
  }, [router]);

  const updateLastActivity = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('last_activity', Date.now().toString());
    }
  }, []);

  const checkInactivity = useCallback(() => {
    if (typeof window === 'undefined') {
      return;
    }

    const lastActivity = localStorage.getItem('last_activity');
    if (!lastActivity) {
      return;
    }

    const timeSinceLastActivity = Date.now() - parseInt(lastActivity);
    
    if (timeSinceLastActivity > INACTIVITY_TIMEOUT) {
      console.log('🔒 Session expired due to inactivity (3 hours), logging out...');
      logout();
    }
  }, [logout]);

  useEffect(() => {
    // Check if we're in browser environment
    if (typeof window === 'undefined') {
      setIsAuthLoading(false);
      return;
    }

    const token = localStorage.getItem('auth_token');
    
    if (token) {
      // Check if token is valid (not expired by JWT)
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        
        if (payload.exp && payload.exp < currentTime) {
          console.log('🔒 Token expired, logging out...');
          logout();
          setIsAuthLoading(false);
          return;
        }
      } catch (error) {
        console.error('Token validation error:', error);
        logout();
        setIsAuthLoading(false);
        return;
      }

      // Check inactivity
      checkInactivity();
      
      // If still valid, set authenticated
      setIsAuthenticated(true);
      updateLastActivity();
      
      // Load user data from localStorage
      const userData = localStorage.getItem('user');
      if (userData) {
        try {
          setUser(JSON.parse(userData));
        } catch (error) {
          console.error('Failed to parse user data:', error);
        }
      }
    }
    
    setIsAuthLoading(false);
  }, [router, logout, checkInactivity, updateLastActivity]);

  // Periodic inactivity check (every 60 seconds)
  useEffect(() => {
    if (!isAuthenticated || typeof window === 'undefined') {
      return;
    }

    const interval = setInterval(() => {
      checkInactivity();
    }, INACTIVITY_CHECK_INTERVAL);

    return () => clearInterval(interval);
  }, [isAuthenticated, checkInactivity]);

  // Track user activity
  useEffect(() => {
    if (!isAuthenticated || typeof window === 'undefined') {
      return;
    }

    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];
    
    const handleActivity = () => {
      updateLastActivity();
    };

    activityEvents.forEach(event => {
      window.addEventListener(event, handleActivity);
    });

    return () => {
      activityEvents.forEach(event => {
        window.removeEventListener(event, handleActivity);
      });
    };
  }, [isAuthenticated, updateLastActivity]);

  return {
    isAuthenticated,
    isAuthLoading: isAuthLoading ?? true,
    user,
    logout
  };
}