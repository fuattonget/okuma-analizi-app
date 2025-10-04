import { useState, useEffect, useCallback } from 'react';
import { apiClient, User } from './api';
import { useAuth } from './useAuth';

export type Role = 'admin' | 'manager' | 'teacher';

export interface Permission {
  user_management: boolean;
  role_management: boolean;
  student_management: boolean;
  text_management: boolean;
  analysis_management: boolean;
  system_access: boolean;
  // Granular permissions
  'student:create': boolean;
  'student:read': boolean;
  'student:view': boolean;
  'student:update': boolean;
  'student:delete': boolean;
  'text:create': boolean;
  'text:read': boolean;
  'text:view': boolean;
  'text:update': boolean;
  'text:delete': boolean;
  'analysis:create': boolean;
  'analysis:read': boolean;
  'analysis:view': boolean;
  'analysis:update': boolean;
  'analysis:delete': boolean;
  'user:create': boolean;
  'user:read': boolean;
  'user:view': boolean;
  'user:update': boolean;
  'user:delete': boolean;
  'role:create': boolean;
  'role:read': boolean;
  'role:view': boolean;
  'role:update': boolean;
  'role:delete': boolean;
  'system:settings': boolean;
  'system:logs': boolean;
  'system:status': boolean;
}

export function useRoles() {
  const { user, isAuthLoading } = useAuth();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadCurrentUser = useCallback(async () => {
    try {
      setIsLoading(true);
      const user = await apiClient.getCurrentUser();
      setCurrentUser(user);
    } catch (error) {
      console.error('Failed to load current user:', error);
      setCurrentUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user && !isAuthLoading) {
      loadCurrentUser();
    } else if (!user && !isAuthLoading) {
      setCurrentUser(null);
      setIsLoading(false);
    }
  }, [user, isAuthLoading, loadCurrentUser]);

  // Use user from useAuth as fallback
  const effectiveUser = currentUser || user;

  const hasRole = useCallback((role: Role): boolean => {
    return effectiveUser?.role === role;
  }, [effectiveUser]);

  const hasAnyRole = useCallback((roles: Role[]): boolean => {
    return effectiveUser ? roles.includes(effectiveUser.role as Role) : false;
  }, [effectiveUser]);

  const hasPermission = useCallback((permission: keyof Permission): boolean => {
    if (!effectiveUser) {
      return false;
    }

    const role = effectiveUser.role;
    
    // Admin has all permissions
    if (role === 'admin') {
      return true;
    }
    
    switch (permission) {
      // Legacy permissions
      case 'user_management':
        return role === 'admin';
      
      case 'role_management':
        return role === 'admin';
      
      case 'student_management':
        return role === 'admin' || role === 'manager';
      
      case 'text_management':
        return role === 'admin' || role === 'manager';
      
      case 'analysis_management':
        return role === 'admin' || role === 'manager';
      
      case 'system_access':
        return role === 'admin';
      
      // Granular permissions
      case 'student:create':
        return role === 'admin' || role === 'manager';
      
      case 'student:read':
      case 'student:view':
        return role === 'admin' || role === 'manager' || role === 'teacher';
      
      case 'student:update':
        return role === 'admin' || role === 'manager';
      
      case 'student:delete':
        return role === 'admin' || role === 'manager';
      
      case 'text:create':
        return role === 'admin' || role === 'manager';
      
      case 'text:read':
      case 'text:view':
        return role === 'admin' || role === 'manager' || role === 'teacher';
      
      case 'text:update':
        return role === 'admin' || role === 'manager';
      
      case 'text:delete':
        return role === 'admin' || role === 'manager';
      
      case 'analysis:create':
        return role === 'admin' || role === 'manager' || role === 'teacher';
      
      case 'analysis:read':
      case 'analysis:view':
        return role === 'admin' || role === 'manager' || role === 'teacher';
      
      case 'analysis:update':
        return role === 'admin' || role === 'manager';
      
      case 'analysis:delete':
        return role === 'admin' || role === 'manager';
      
      case 'user:create':
      case 'user:read':
      case 'user:view':
      case 'user:update':
      case 'user:delete':
        return role === 'admin';
      
      case 'role:create':
      case 'role:read':
      case 'role:view':
      case 'role:update':
      case 'role:delete':
        return role === 'admin';
      
      case 'system:settings':
      case 'system:logs':
      case 'system:status':
        return role === 'admin';
      
      default:
        return false;
    }
  }, [effectiveUser]);

  const hasAnyPermission = useCallback((permissions: (keyof Permission)[]): boolean => {
    return permissions.some(permission => hasPermission(permission));
  }, [hasPermission]);

  const hasAllPermissions = useCallback((permissions: (keyof Permission)[]): boolean => {
    return permissions.every(permission => hasPermission(permission));
  }, [hasPermission]);

  const getPermissions = useCallback((): Permission => {
    if (!effectiveUser) {
      return {
        user_management: false,
        role_management: false,
        student_management: false,
        text_management: false,
        analysis_management: false,
        system_access: false,
        'student:create': false,
        'student:read': false,
        'student:view': false,
        'student:update': false,
        'student:delete': false,
        'text:create': false,
        'text:read': false,
        'text:view': false,
        'text:update': false,
        'text:delete': false,
        'analysis:create': false,
        'analysis:read': false,
        'analysis:view': false,
        'analysis:update': false,
        'analysis:delete': false,
        'user:create': false,
        'user:read': false,
        'user:view': false,
        'user:update': false,
        'user:delete': false,
        'role:create': false,
        'role:read': false,
        'role:view': false,
        'role:update': false,
        'role:delete': false,
        'system:settings': false,
        'system:logs': false,
        'system:status': false,
      };
    }

    return {
      user_management: hasPermission('user_management'),
      role_management: hasPermission('role_management'),
      student_management: hasPermission('student_management'),
      text_management: hasPermission('text_management'),
      analysis_management: hasPermission('analysis_management'),
      system_access: hasPermission('system_access'),
      'student:create': hasPermission('student:create'),
      'student:read': hasPermission('student:read'),
      'student:view': hasPermission('student:view'),
      'student:update': hasPermission('student:update'),
      'student:delete': hasPermission('student:delete'),
      'text:create': hasPermission('text:create'),
      'text:read': hasPermission('text:read'),
      'text:view': hasPermission('text:view'),
      'text:update': hasPermission('text:update'),
      'text:delete': hasPermission('text:delete'),
      'analysis:create': hasPermission('analysis:create'),
      'analysis:read': hasPermission('analysis:read'),
      'analysis:view': hasPermission('analysis:view'),
      'analysis:update': hasPermission('analysis:update'),
      'analysis:delete': hasPermission('analysis:delete'),
      'user:create': hasPermission('user:create'),
      'user:read': hasPermission('user:read'),
      'user:view': hasPermission('user:view'),
      'user:update': hasPermission('user:update'),
      'user:delete': hasPermission('user:delete'),
      'role:create': hasPermission('role:create'),
      'role:read': hasPermission('role:read'),
      'role:view': hasPermission('role:view'),
      'role:update': hasPermission('role:update'),
      'role:delete': hasPermission('role:delete'),
      'system:settings': hasPermission('system:settings'),
      'system:logs': hasPermission('system:logs'),
      'system:status': hasPermission('system:status'),
    };
  }, [effectiveUser, hasPermission]);

  const getRoleDisplayName = useCallback((role: string): string => {
    switch (role) {
      case 'admin':
        return 'Yönetici';
      case 'manager':
        return 'Müdür';
      case 'teacher':
        return 'Öğretmen';
      default:
        return role;
    }
  }, []);

  const getRoleColor = useCallback((role: string): string => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'manager':
        return 'bg-blue-100 text-blue-800';
      case 'teacher':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }, []);

  return {
    currentUser: effectiveUser,
    isLoading,
    hasRole,
    hasAnyRole,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    getPermissions,
    getRoleDisplayName,
    getRoleColor,
    refreshUser: loadCurrentUser,
  };
}
