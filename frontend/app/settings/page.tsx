'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, User, Role } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { useRoles } from '@/lib/useRoles';
import Navigation from '@/components/Navigation';
import Breadcrumbs from '@/components/Breadcrumbs';
import { formatTurkishDate } from '@/lib/dateUtils';
import { themeColors, combineThemeClasses, componentClasses } from '@/lib/theme';
import { PERMISSION_GROUPS, GROUP_COLORS, getPermissionLabel } from '@/lib/permissions';
import * as Icons from '@/components/Icon';

const {
  UserIcon,
  SearchIcon,
  PlusIcon,
  EditIcon,
  DeleteIcon,
  RefreshIcon,
  FilterIcon,
  CrossIcon,
  CheckIcon,
  LockIcon,
  UnlockIcon,
  EyeIcon,
  EyeOffIcon,
  SettingsIcon,
  ShieldIcon,
  StudentsIcon,
  TextsIcon,
  AnalysesIcon
} = Icons;

type TabType = 'users' | 'roles';

export default function SettingsPage() {
  const router = useRouter();
  const { isAuthenticated, isAuthLoading, user } = useAuth();
  const { hasPermission } = useRoles();
  const [activeTab, setActiveTab] = useState<TabType>('users');
  
  // User management state
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [showUserModal, setShowUserModal] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  // User form state
  const [userForm, setUserForm] = useState({
    email: '',
    username: '',
    password: '',
    role: '',
    is_active: true
  });

  // Role form state
  const [roleForm, setRoleForm] = useState({
    name: '',
    display_name: '',
    description: '',
    permissions: [] as string[]
  });

  // Available permissions
  const [availablePermissions, setAvailablePermissions] = useState<string[]>([]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isAuthLoading, router]);

  // Check permissions - allow access if user has any read or management permission
  useEffect(() => {
    if (!isAuthLoading && isAuthenticated) {
      const canAccess = hasPermission('user_management') || 
                       hasPermission('role_management') ||
                       hasPermission('user:read') ||
                       hasPermission('role:read');
      if (!canAccess) {
        router.push('/');
      }
    }
  }, [isAuthenticated, isAuthLoading, hasPermission, router]);

  // Load data
  const loadUsers = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await apiClient.getUsers(
        1,
        100,
        searchTerm || undefined,
        roleFilter || undefined
      );
      setUsers(response.users);
    } catch (error) {
      console.error('Failed to load users:', error);
      setError('Kullanıcılar yüklenirken hata oluştu');
    } finally {
      setIsLoading(false);
    }
  }, [searchTerm, roleFilter]);

  const loadRoles = useCallback(async () => {
    // Only load roles if user has permission
    const hasRoleRead = hasPermission('role:read');
    const hasRoleMgmt = hasPermission('role_management');
    console.log('🔍 loadRoles: Checking permissions', { hasRoleRead, hasRoleMgmt });
    
    if (!hasRoleRead && !hasRoleMgmt) {
      console.log('⛔ No permission to load roles');
      setRoles([]);
      return;
    }
    
    try {
      console.log('✅ Loading roles...');
      const response = await apiClient.getRoles();
      console.log('✅ Roles loaded:', response.roles.length);
      setRoles(response.roles);
    } catch (error) {
      console.error('Failed to load roles:', error);
      setRoles([]);
    }
  }, [hasPermission]);

  const loadAvailablePermissions = useCallback(async () => {
    try {
      const permissions = await apiClient.getAvailablePermissions();
      setAvailablePermissions(permissions);
    } catch (error) {
      console.error('Failed to load permissions:', error);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated && !isAuthLoading) {
      loadUsers();
      loadRoles();
      loadAvailablePermissions();
    }
  }, [isAuthenticated, isAuthLoading, loadUsers, loadRoles, loadAvailablePermissions]);

  // User management functions
  const handleCreateUser = async () => {
    try {
      await apiClient.createUser(userForm);
      setShowUserModal(false);
      setUserForm({ email: '', username: '', password: '', role: '', is_active: true });
      loadUsers();
    } catch (error) {
      console.error('Failed to create user:', error);
      setError('Kullanıcı oluşturulurken hata oluştu');
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser) return;
    
    try {
      await apiClient.updateUser(editingUser.id, userForm);
      setShowUserModal(false);
      setEditingUser(null);
      setUserForm({ email: '', username: '', password: '', role: '', is_active: true });
      loadUsers();
    } catch (error) {
      console.error('Failed to update user:', error);
      setError('Kullanıcı güncellenirken hata oluştu');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Bu kullanıcıyı silmek istediğinizden emin misiniz?')) return;
    
    try {
      await apiClient.deleteUser(userId);
      loadUsers();
    } catch (error) {
      console.error('Failed to delete user:', error);
      setError('Kullanıcı silinirken hata oluştu');
    }
  };

  const handleResetPassword = async (userId: string) => {
    if (!confirm('Bu kullanıcının şifresini sıfırlamak istediğinizden emin misiniz?')) return;
    
    try {
      await apiClient.resetUserPassword(userId, 'password123');
      alert('Şifre sıfırlandı: password123');
    } catch (error) {
      console.error('Failed to reset password:', error);
      setError('Şifre sıfırlanırken hata oluştu');
    }
  };

  // Role management functions
  const handleCreateRole = async () => {
    try {
      await apiClient.createRole(roleForm);
      setShowRoleModal(false);
      setRoleForm({ name: '', display_name: '', description: '', permissions: [] });
      loadRoles();
    } catch (error) {
      console.error('Failed to create role:', error);
      setError('Rol oluşturulurken hata oluştu');
    }
  };

  const handleUpdateRole = async () => {
    if (!editingRole) return;
    
    try {
      await apiClient.updateRole(editingRole.id, roleForm);
      setShowRoleModal(false);
      setEditingRole(null);
      setRoleForm({ name: '', display_name: '', description: '', permissions: [] });
      loadRoles();
    } catch (error) {
      console.error('Failed to update role:', error);
      setError('Rol güncellenirken hata oluştu');
    }
  };

  const handleDeleteRole = async (roleId: string) => {
    if (!confirm('Bu rolü silmek istediğinizden emin misiniz?')) return;
    
    try {
      await apiClient.deleteRole(roleId);
      loadRoles();
    } catch (error) {
      console.error('Failed to delete role:', error);
      setError('Rol silinirken hata oluştu');
    }
  };

  // Modal handlers
  const openUserModal = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setUserForm({
        email: user.email,
        username: user.username,
        password: '',
        role: user.role,
        is_active: user.is_active
      });
    } else {
      setEditingUser(null);
      setUserForm({ email: '', username: '', password: '', role: '', is_active: true });
    }
    setShowUserModal(true);
  };

  const openRoleModal = (role?: Role) => {
    if (role) {
      setEditingRole(role);
      setRoleForm({
        name: role.name,
        display_name: role.display_name || '',
        description: role.description || '',
        permissions: role.permissions || []
      });
    } else {
      setEditingRole(null);
      setRoleForm({ name: '', display_name: '', description: '', permissions: [] });
    }
    setShowRoleModal(true);
  };

  const togglePermission = (permission: string) => {
    setRoleForm(prev => ({
      ...prev,
      permissions: prev.permissions.includes(permission)
        ? prev.permissions.filter(p => p !== permission)
        : [...prev.permissions, permission]
    }));
  };

  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
        <Navigation />
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">Yükleniyor...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-900">
      <Navigation />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Breadcrumbs
          items={[
            { label: 'Ana Sayfa', href: '/' },
            { label: 'Ayarlar', href: '/settings' }
          ]}
        />

        <div className="mt-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center">
              <SettingsIcon size="lg" className="mr-3" />
              Sistem Ayarları
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Kullanıcı ve rol yönetimi
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <CrossIcon size="sm" className="text-red-400" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
                </div>
                <div className="ml-auto pl-3">
                  <button
                    onClick={() => setError(null)}
                    className="text-red-400 hover:text-red-600"
                  >
                    <CrossIcon size="sm" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('users')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'users'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <UserIcon size="sm" className="inline mr-2" />
                Kullanıcı Yönetimi
              </button>
              <button
                onClick={() => setActiveTab('roles')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'roles'
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <ShieldIcon size="sm" className="inline mr-2" />
                Rol Yönetimi
              </button>
            </nav>
          </div>

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div>
              {/* Users Header */}
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Kullanıcı Yönetimi
                  </h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Sistem kullanıcılarını yönetin
                  </p>
                </div>
                {(hasPermission('user:create') || hasPermission('user_management')) && (
                  <button
                    onClick={() => openUserModal()}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <PlusIcon size="sm" className="mr-2" />
                    Yeni Kullanıcı
                  </button>
                )}
              </div>

              {/* Users Filters */}
              <div className="bg-white dark:bg-slate-800 rounded-lg shadow p-6 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Arama
                    </label>
                    <div className="relative">
                      <SearchIcon size="sm" className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Email veya kullanıcı adı ara..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Rol
                    </label>
                    <select
                      value={roleFilter}
                      onChange={(e) => setRoleFilter(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                    >
                      <option value="">Tüm Roller</option>
                      {roles.map((role) => (
                        <option key={role.id} value={role.name}>
                          {role.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={() => {
                        setSearchTerm('');
                        setRoleFilter('');
                      }}
                      className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-slate-700 hover:bg-gray-50 dark:hover:bg-slate-600"
                    >
                      <FilterIcon size="sm" className="mr-2" />
                      Filtreleri Temizle
                    </button>
                  </div>
                </div>
              </div>

              {/* Users List */}
              <div className="bg-white dark:bg-slate-800 rounded-lg shadow overflow-hidden">
                {isLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
                      <p className="mt-2 text-gray-600 dark:text-gray-400">Kullanıcılar yükleniyor...</p>
                    </div>
                  </div>
                ) : users.length === 0 ? (
                  <div className="text-center py-12">
                    <UserIcon size="lg" className="mx-auto text-gray-400" />
                    <p className="mt-2 text-gray-600 dark:text-gray-400">Henüz kullanıcı bulunmuyor</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                      <thead className="bg-gray-50 dark:bg-slate-700">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Kullanıcı
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Rol
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Durum
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            Oluşturulma
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                            İşlemler
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-200 dark:divide-gray-700">
                        {users.map((user) => (
                          <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-slate-700">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="flex-shrink-0 h-10 w-10">
                                  <div className="h-10 w-10 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
                                    <span className="text-sm font-medium text-indigo-600 dark:text-indigo-300">
                                      {user.username.charAt(0).toUpperCase()}
                                    </span>
                                  </div>
                                </div>
                                <div className="ml-4">
                                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                                    {user.username}
                                  </div>
                                  <div className="text-sm text-gray-500 dark:text-gray-400">
                                    {user.email}
                                  </div>
                                </div>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                {user.role}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                user.is_active
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              }`}>
                                {user.is_active ? 'Aktif' : 'Pasif'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                              {formatTurkishDate(user.created_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                              <div className="flex justify-end space-x-2">
                                {(hasPermission('user:update') || hasPermission('user_management')) && (
                                  <button
                                    onClick={() => openUserModal(user)}
                                    className="text-indigo-600 hover:text-indigo-900 dark:text-indigo-400 dark:hover:text-indigo-300"
                                    title="Düzenle"
                                  >
                                    <EditIcon size="sm" />
                                  </button>
                                )}
                                {(hasPermission('user:update') || hasPermission('user_management')) && (
                                  <button
                                    onClick={() => handleResetPassword(user.id)}
                                    className="text-yellow-600 hover:text-yellow-900 dark:text-yellow-400 dark:hover:text-yellow-300"
                                    title="Şifre Sıfırla"
                                  >
                                    <LockIcon size="sm" />
                                  </button>
                                )}
                                {(hasPermission('user:delete') || hasPermission('user_management')) && (
                                  <button
                                    onClick={() => handleDeleteUser(user.id)}
                                    className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                                    title="Sil"
                                  >
                                    <DeleteIcon size="sm" />
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Roles Tab */}
          {activeTab === 'roles' && (
            <div>
              {/* Check if user has permission to view roles */}
              {!hasPermission('role:read') && !hasPermission('role_management') ? (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
                  <div className="flex items-center">
                    <ShieldIcon size="lg" className="text-yellow-600 dark:text-yellow-400 mr-4" />
                    <div>
                      <h3 className="text-lg font-semibold text-yellow-800 dark:text-yellow-200">
                        Yetki Gerekli
                      </h3>
                      <p className="text-yellow-700 dark:text-yellow-300 mt-1">
                        Rol listesini görüntülemek için <code className="bg-yellow-100 dark:bg-yellow-900 px-2 py-0.5 rounded">role:read</code> yetkisine ihtiyacınız var.
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <>
                  {/* Roles Header */}
                  <div className="flex justify-between items-center mb-6">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                        Rol Yönetimi
                      </h2>
                      <p className="text-gray-600 dark:text-gray-400">
                        Sistem rollerini ve yetkilerini yönetin
                      </p>
                    </div>
                    {(hasPermission('role:create') || hasPermission('role_management')) && (
                      <button
                        onClick={() => openRoleModal()}
                        className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        <PlusIcon size="sm" className="mr-2" />
                        Yeni Rol
                      </button>
                    )}
                  </div>

                  {/* Roles List - Card View */}
                  <div>
                {roles.length === 0 ? (
                  <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-lg shadow">
                    <ShieldIcon size="lg" className="mx-auto text-gray-400" />
                    <p className="mt-2 text-gray-600 dark:text-gray-400">Henüz rol bulunmuyor</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {roles.map((role) => {
                      // Grup bazında permission sayılarını hesapla
                      const permissionsByGroup = PERMISSION_GROUPS.map(group => ({
                        ...group,
                        count: role.permissions?.filter(p => 
                          group.permissions.some(gp => gp.key === p)
                        ).length || 0
                      })).filter(g => g.count > 0);

                      return (
                        <div 
                          key={role.id} 
                          className="bg-white dark:bg-slate-800 rounded-lg shadow-md hover:shadow-lg transition-shadow p-6 border border-gray-200 dark:border-gray-700"
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex items-center space-x-3">
                              <div className="flex-shrink-0">
                                <div className="w-12 h-12 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center">
                                  <ShieldIcon size="md" className="text-indigo-600 dark:text-indigo-400" />
                                </div>
                              </div>
                              <div>
                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                  {role.display_name || role.name}
                                </h3>
                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                  {role.name}
                                </p>
                              </div>
                            </div>
                          </div>

                          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4 min-h-[40px]">
                            {role.description || 'Açıklama yok'}
                          </p>

                          {/* Permission Groups Summary */}
                          <div className="mb-4">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-xs font-medium text-gray-500 dark:text-gray-400">
                                Yetkiler
                              </span>
                              <span className="text-xs font-semibold text-indigo-600 dark:text-indigo-400">
                                {role.permissions?.length || 0} yetki
                              </span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {permissionsByGroup.map(group => {
                                const groupColor = GROUP_COLORS[group.color as keyof typeof GROUP_COLORS];
                                const GroupIcon = (Icons as any)[group.icon] || ShieldIcon;
                                return (
                                  <div
                                    key={group.id}
                                    className={`inline-flex items-center space-x-1 px-2 py-1 rounded-md text-xs font-medium ${groupColor.badge}`}
                                    title={`${group.label}: ${group.count} yetki`}
                                  >
                                    <GroupIcon size="xs" />
                                    <span>{group.count}</span>
                                  </div>
                                );
                              })}
                            </div>
                          </div>

                          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {formatTurkishDate(role.created_at)}
                            </div>
                            {(hasPermission('role:update') || hasPermission('role:delete') || hasPermission('role_management')) && (
                              <div className="flex space-x-2">
                                {(hasPermission('role:update') || hasPermission('role_management')) && (
                                  <button
                                    onClick={() => openRoleModal(role)}
                                    className="p-2 text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-md transition-colors"
                                    title="Düzenle"
                                  >
                                    <EditIcon size="sm" />
                                  </button>
                                )}
                                {(hasPermission('role:delete') || hasPermission('role_management')) && (
                                  <button
                                    onClick={() => handleDeleteRole(role.id)}
                                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-md transition-colors"
                                    title="Sil"
                                  >
                                    <DeleteIcon size="sm" />
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* User Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white dark:bg-slate-800">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {editingUser ? 'Kullanıcı Düzenle' : 'Yeni Kullanıcı'}
                </h3>
                <button
                  onClick={() => setShowUserModal(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <CrossIcon size="sm" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    E-posta
                  </label>
                  <input
                    type="email"
                    value={userForm.email}
                    onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Kullanıcı Adı
                  </label>
                  <input
                    type="text"
                    value={userForm.username}
                    onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Şifre {editingUser && '(Boş bırakırsanız değişmez)'}
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={userForm.password}
                      onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                      className="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                      required={!editingUser}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    >
                      {showPassword ? <EyeOffIcon size="sm" /> : <EyeIcon size="sm" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Rol
                  </label>
                  <select
                    value={userForm.role}
                    onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                    required
                  >
                    <option value="">Rol seçin</option>
                    {roles.map((role) => (
                      <option key={role.id} value={role.name}>
                        {role.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    checked={userForm.is_active}
                    onChange={(e) => setUserForm({ ...userForm, is_active: e.target.checked })}
                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                    Aktif
                  </label>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowUserModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-slate-600 hover:bg-gray-200 dark:hover:bg-slate-500 rounded-md"
                >
                  İptal
                </button>
                <button
                  onClick={editingUser ? handleUpdateUser : handleCreateUser}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                >
                  {editingUser ? 'Güncelle' : 'Oluştur'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Role Modal */}
      {showRoleModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-md bg-white dark:bg-slate-800">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  {editingRole ? 'Rol Düzenle' : 'Yeni Rol'}
                </h3>
                <button
                  onClick={() => setShowRoleModal(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <CrossIcon size="sm" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Rol Adı
                  </label>
                  <input
                    type="text"
                    value={roleForm.name}
                    onChange={(e) => setRoleForm({ ...roleForm, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Görünen Ad
                  </label>
                  <input
                    type="text"
                    value={roleForm.display_name}
                    onChange={(e) => setRoleForm({ ...roleForm, display_name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Açıklama
                  </label>
                  <textarea
                    value={roleForm.description}
                    onChange={(e) => setRoleForm({ ...roleForm, description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Yetkiler
                    <span className="ml-2 text-xs font-normal text-gray-500 dark:text-gray-400">
                      ({roleForm.permissions.length} yetki seçili)
                    </span>
                  </label>
                  <div className="space-y-4 max-h-96 overflow-y-auto border border-gray-300 dark:border-gray-600 rounded-lg p-4">
                    {PERMISSION_GROUPS.map((group) => {
                      const groupColor = GROUP_COLORS[group.color as keyof typeof GROUP_COLORS];
                      const groupPermissions = group.permissions.filter(p => 
                        availablePermissions.includes(p.key)
                      );
                      
                      if (groupPermissions.length === 0) return null;
                      
                      const selectedInGroup = groupPermissions.filter(p => 
                        roleForm.permissions.includes(p.key)
                      ).length;
                      
                      // Get icon component dynamically
                      const IconComponent = (Icons as any)[group.icon] || ShieldIcon;
                      
                      return (
                        <div key={group.id} className={`border ${groupColor.border} rounded-lg p-4 ${groupColor.bg}`}>
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center space-x-2">
                              <IconComponent size="md" className={groupColor.text} />
                              <h4 className={`font-semibold ${groupColor.text}`}>
                                {group.label}
                              </h4>
                            </div>
                            {selectedInGroup > 0 && (
                              <span className={`text-xs px-2 py-1 rounded-full ${groupColor.badge}`}>
                                {selectedInGroup}/{groupPermissions.length}
                              </span>
                            )}
                          </div>
                          <div className="space-y-2">
                            {groupPermissions.map((permission) => (
                              <label 
                                key={permission.key} 
                                className="flex items-start space-x-3 p-2 rounded-md hover:bg-white/50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors"
                              >
                                <input
                                  type="checkbox"
                                  checked={roleForm.permissions.includes(permission.key)}
                                  onChange={() => togglePermission(permission.key)}
                                  className="h-4 w-4 mt-0.5 text-indigo-600 focus:ring-indigo-500 border-gray-300 dark:border-gray-600 rounded"
                                />
                                <div className="flex-1">
                                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                                    {permission.label}
                                  </div>
                                  <div className="text-xs text-gray-500 dark:text-gray-400">
                                    {permission.description}
                                  </div>
                                </div>
                              </label>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowRoleModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-slate-600 hover:bg-gray-200 dark:hover:bg-slate-500 rounded-md"
                >
                  İptal
                </button>
                <button
                  onClick={editingRole ? handleUpdateRole : handleCreateRole}
                  className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md"
                >
                  {editingRole ? 'Güncelle' : 'Oluştur'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
