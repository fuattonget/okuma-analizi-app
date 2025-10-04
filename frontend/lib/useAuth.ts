import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

export function useAuth() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Check if we're in browser environment
    if (typeof window === 'undefined') {
      setIsAuthLoading(false);
      return;
    }

    const token = localStorage.getItem('auth_token');
    
    if (token) {
      // Check if token is expired
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        
        if (payload.exp && payload.exp < currentTime) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          setIsAuthenticated(false);
          setIsAuthLoading(false);
          setUser(null);
          router.push('/login');
        } else {
          setIsAuthenticated(true);
          setIsAuthLoading(false);
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
      } catch (error) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setIsAuthLoading(false);
        setUser(null);
        router.push('/login');
      }
    } else {
      setIsAuthenticated(false);
      setIsAuthLoading(false);
      setUser(null);
    }
  }, [router]);

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