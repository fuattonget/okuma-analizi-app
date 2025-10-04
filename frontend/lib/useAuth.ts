import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';

export function useAuth() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    console.log('🔍 useAuth useEffect triggered');
    
    // Check if we're in browser environment
    if (typeof window === 'undefined') {
      console.log('🔍 useAuth: Server side, setting loading false');
      setIsAuthLoading(false);
      return;
    }

    console.log('🔍 useAuth: Client side, checking token');
    const token = localStorage.getItem('auth_token');
    console.log('🔍 useAuth: Token found:', !!token);
    
    if (token) {
      // Check if token is expired
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        
        if (payload.exp && payload.exp < currentTime) {
          console.log('🔍 useAuth: Token expired, clearing and redirecting');
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          setIsAuthenticated(false);
          setIsAuthLoading(false);
          setUser(null);
          router.push('/login');
        } else {
          console.log('🔍 useAuth: Token valid, setting authenticated true');
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
        console.log('🔍 useAuth: Invalid token format, clearing and redirecting');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setIsAuthLoading(false);
        setUser(null);
        router.push('/login');
      }
    } else {
      console.log('🔍 useAuth: No token, setting authenticated false');
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