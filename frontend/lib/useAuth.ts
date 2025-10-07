import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

export function useAuth() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [user, setUser] = useState(null);

  const checkTokenExpiration = useCallback(() => {
    if (typeof window === 'undefined') {
      return false;
    }

    const token = localStorage.getItem('auth_token');
    
    if (!token) {
      return false;
    }

    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Math.floor(Date.now() / 1000);
      
      if (payload.exp && payload.exp < currentTime) {
        console.log('🔒 Token expired, logging out...');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setUser(null);
        router.push('/login');
        return false;
      }
      return true;
    } catch (error) {
      console.error('Token validation error:', error);
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      setIsAuthenticated(false);
      setUser(null);
      router.push('/login');
      return false;
    }
  }, [router]);

  useEffect(() => {
    // Check if we're in browser environment
    if (typeof window === 'undefined') {
      setIsAuthLoading(false);
      return;
    }

    const token = localStorage.getItem('auth_token');
    
    if (token) {
      // Initial token check
      const isValid = checkTokenExpiration();
      
      if (isValid) {
        setIsAuthenticated(true);
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
    }
    
    setIsAuthLoading(false);
  }, [router, checkTokenExpiration]);

  // Periodic token expiration check (every 60 seconds)
  useEffect(() => {
    if (!isAuthenticated || typeof window === 'undefined') {
      return;
    }

    const interval = setInterval(() => {
      checkTokenExpiration();
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [isAuthenticated, checkTokenExpiration]);

  const logout = useCallback(() => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
    setIsAuthenticated(false);
    setIsAuthLoading(false);
    setUser(null);
    router.push('/login');
  }, [router]);

  return {
    isAuthenticated,
    isAuthLoading: isAuthLoading ?? true,
    user,
    logout
  };
}