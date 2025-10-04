'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient, Student } from '@/lib/api';
import { useAuth } from '@/lib/useAuth';
import { useRoles } from '@/lib/useRoles';
import Navigation from '@/components/Navigation';
import Breadcrumbs from '@/components/Breadcrumbs';
import Tooltip, { InfoTooltip, ActionTooltip } from '@/components/Tooltip';
import { DeactivateConfirmationDialog, ActivateConfirmationDialog } from '@/components/ConfirmationDialog';
import { 
  AddIcon, 
  SearchIcon, 
  FilterIcon, 
  RefreshIcon, 
  ViewIcon, 
  EditIcon, 
  LockIcon,
  UnlockIcon,
  UserIcon,
  GradeIcon,
  BookIcon,
  CalendarIcon,
  ClockIcon,
  StudentsIcon,
  AnalysisIcon,
  LightbulbIcon,
  CrossIcon,
  CheckIcon
} from '@/components/Icon';
import classNames from 'classnames';
import { formatTurkishDate } from '@/lib/dateUtils';
import { themeColors, combineThemeClasses, componentClasses } from '@/lib/theme';

export default function StudentsPage() {
  const router = useRouter();
  const { isAuthenticated, isAuthLoading } = useAuth();
  const { hasPermission } = useRoles();
  
  // Debug logging
  console.log('🔍 StudentsPage render:', { isAuthenticated, isAuthLoading });
  
  // State management
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingStudent, setEditingStudent] = useState<Student | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Confirmation dialog states
  const [showDeactivateDialog, setShowDeactivateDialog] = useState(false);
  const [showActivateDialog, setShowActivateDialog] = useState(false);
  const [showEditConfirmDialog, setShowEditConfirmDialog] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Advanced Filter and search states
  const [filters, setFilters] = useState({
    search: '',
    grade: 'all' as number | 'all',
    status: 'active' as 'all' | 'active' | 'inactive',
    dateRange: {
      start: '',
      end: ''
    },
    createdBy: 'all' as string | 'all',
    sortBy: 'created_at' as 'created_at' | 'name' | 'grade' | 'status',
    sortOrder: 'desc' as 'asc' | 'desc'
  });
  
  // Advanced filter visibility
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [activeFilterCount, setActiveFilterCount] = useState(0);
  
  // Table loading state
  const [tableLoading, setTableLoading] = useState(false);
  
  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [totalStudents, setTotalStudents] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [customPageSize, setCustomPageSize] = useState('');
  
  // Form data
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    grade: 1
  });
  
  // Form validation errors
  const [formErrors, setFormErrors] = useState({
    first_name: '',
    last_name: '',
    grade: ''
  });


  // Close modal on ESC key
  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && showModal) {
        handleCloseModal();
      }
    };

    if (showModal) {
      document.addEventListener('keydown', handleEsc);
    }

    return () => {
      document.removeEventListener('keydown', handleEsc);
    };
  }, [showModal]);

  // Auto-hide success/error messages
  useEffect(() => {
    if (success || error) {
      const timer = setTimeout(() => {
        setSuccess('');
        setError('');
      }, 8000); // 8 saniye
      return () => clearTimeout(timer);
    }
  }, [success, error]);

  // Load students with current filters (table only update)
  const loadStudents = useCallback(async (page = currentPage, size = pageSize, customFilters = filters, isInitialLoad = false) => {
    console.log('🔍 loadStudents called with:', { page, size, customFilters, isInitialLoad });
    
    try {
      console.log('🔍 loadStudents: Setting loading states');
      setTableLoading(true);
      // Only set main loading state for initial load, not for filters/search
      if (isInitialLoad) {
        setLoading(true);
      }
      setError('');
      console.log('🔄 Loading students...', { page, size, filters: customFilters });
      
      // Prepare filter parameters
      const grade = customFilters.grade !== 'all' ? customFilters.grade : undefined;
      const search = customFilters.search.trim() || undefined;
      const isActive = customFilters.status === 'all' ? undefined : customFilters.status === 'active';
      const createdAfter = customFilters.dateRange.start || undefined;
      const createdBefore = customFilters.dateRange.end || undefined;
      const sortBy = customFilters.sortBy;
      const sortOrder = customFilters.sortOrder;
      
      console.log('🔍 loadStudents: Prepared filter params:', { 
        grade, search, isActive, createdAfter, createdBefore, sortBy, sortOrder 
      });
      
      console.log('🔍 loadStudents: Calling API...');
      const response = await apiClient.getStudents(
        page, 
        size, 
        grade, 
        search, 
        isActive,
        createdAfter,
        createdBefore,
        sortBy,
        sortOrder
      );
      console.log('📊 Students response:', response);
      
      // Update only table data, not entire page
      console.log('🔍 loadStudents: Updating state...');
      setStudents(response.students || []);
      setTotalStudents(response.total || 0);
      setTotalPages(response.total_pages || 0);
      console.log('✅ Students loaded:', response.students?.length || 0, 'students');
    } catch (error) {
      console.error('❌ Failed to load students:', error);
      setError('❌ Öğrenciler yüklenirken hata oluştu. Lütfen sayfayı yenileyin.');
    } finally {
      console.log('🔍 loadStudents: Setting loading states false');
      setTableLoading(false);
      // Only set main loading state to false for initial load
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  }, []);

  // Handle token expiration and redirect
  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      console.log('🔍 StudentsPage: User not authenticated, redirecting to login');
      router.push('/login');
    }
  }, [isAuthenticated, isAuthLoading, router]);

  // Load students on component mount
  useEffect(() => {
    console.log('🔍 StudentsPage: Mount useEffect triggered', { isAuthenticated });
    if (isAuthenticated) {
      console.log('🔍 StudentsPage: Calling loadStudents from mount');
      loadStudents(1, pageSize, filters, true); // isInitialLoad = true
    }
  }, [isAuthenticated]);

  // Apply filters with smart debounce
  useEffect(() => {
    console.log('🔍 StudentsPage: Filters useEffect triggered', { isAuthenticated, filters });
    if (isAuthenticated) {
      const debounceTime = filters.search ? 500 : 300; // Search: 500ms, others: 300ms
      console.log('🔍 StudentsPage: Setting timeout for loadStudents', { debounceTime });
      const timeoutId = setTimeout(() => {
        console.log('🔍 StudentsPage: Timeout triggered, calling loadStudents');
        loadStudents(1, pageSize, filters, false); // isInitialLoad = false for filters
      }, debounceTime);
      
      return () => {
        console.log('🔍 StudentsPage: Cleaning up timeout');
        clearTimeout(timeoutId);
      };
    }
  }, [filters, isAuthenticated, pageSize]);

  // Pagination functions
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    loadStudents(page, pageSize, filters, false); // isInitialLoad = false
  };

  const handlePageSizeChange = (size: number) => {
    setPageSize(size);
    setCurrentPage(1);
    loadStudents(1, size, filters, false); // isInitialLoad = false
  };

  const handleCustomPageSize = () => {
    const size = parseInt(customPageSize);
    if (size > 0 && size <= 100) {
      handlePageSizeChange(size);
      setCustomPageSize('');
    }
  };

  const validateForm = () => {
    const errors = { first_name: '', last_name: '', grade: '' };
    let isValid = true;

    // First name validation
    if (!formData.first_name.trim()) {
      errors.first_name = 'Ad gereklidir';
      isValid = false;
    } else if (formData.first_name.trim().length < 2) {
      errors.first_name = 'Ad en az 2 karakter olmalıdır';
      isValid = false;
    }

    // Last name validation
    if (!formData.last_name.trim()) {
      errors.last_name = 'Soyad gereklidir';
      isValid = false;
    } else if (formData.last_name.trim().length < 2) {
      errors.last_name = 'Soyad en az 2 karakter olmalıdır';
      isValid = false;
    }

    // Grade validation
    if (formData.grade === undefined || formData.grade === null || (formData.grade < 0 || formData.grade > 6)) {
      errors.grade = 'Geçerli bir sınıf seviyesi seçin';
      isValid = false;
    }


    setFormErrors(errors);
    return isValid;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    console.log('🔍 Form submission started:', formData);
    
    if (!validateForm()) {
      console.log('❌ Form validation failed:', formErrors);
      return;
    }

    setShowEditConfirmDialog(true);
  };

  const confirmSubmit = async () => {
    setIsSubmitting(true);
    setError('');
    setSuccess('');

    try {
      const studentData = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        grade: formData.grade,
      };

      console.log('📤 Sending student data:', studentData);

      if (editingStudent) {
        // Update existing student
        console.log('🔄 Updating student:', editingStudent.id);
        await apiClient.updateStudent(editingStudent.id, studentData);
        setSuccess(`🎉 ${studentData.first_name} ${studentData.last_name} adlı öğrenci başarıyla güncellendi!`);
        console.log('✅ Student updated successfully');
      } else {
        // Create new student
        console.log('➕ Creating new student');
        const newStudent = await apiClient.createStudent(studentData);
        setSuccess(`🎉 ${studentData.first_name} ${studentData.last_name} adlı öğrenci başarıyla eklendi!`);
        console.log('✅ Student created successfully:', newStudent);
      }

      // Reload students
      console.log('🔄 Reloading students list...');
      await loadStudents(1, pageSize, filters, false); // isInitialLoad = false
      
      // Reset form and close modal
      handleCloseModal();
      setShowEditConfirmDialog(false);
      
    } catch (error: any) {
      console.error('❌ Failed to save student:', error);
      console.error('❌ Error response:', error.response?.data);
      if (error.response?.data?.detail) {
        if (error.response.data.detail.includes('Student number already exists')) {
          setError('❌ Bu öğrenci numarası zaten kullanılıyor. Lütfen farklı bir numara girin.');
        } else {
          setError(`❌ ${error.response.data.detail}`);
        }
      } else {
        setError('❌ Öğrenci kaydedilemedi. Lütfen tekrar deneyin.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (student: Student) => {
    setEditingStudent(student);
    setFormData({
      first_name: student.first_name,
      last_name: student.last_name,
      grade: student.grade,
    });
    setFormErrors({ first_name: '', last_name: '', grade: '' });
    setError('');
    setSuccess('');
    setShowModal(true);
  };

  const handleDelete = (student: Student) => {
    console.log('🔄 handleDelete called for student:', student.first_name, student.last_name);
    setSelectedStudent(student);
    setShowDeactivateDialog(true);
  };

  const handleActivate = (student: Student) => {
    console.log('🔄 handleActivate called for student:', student.first_name, student.last_name);
    setSelectedStudent(student);
    setShowActivateDialog(true);
  };

  const handleDeactivateConfirm = async () => {
    if (!selectedStudent) return;

    setIsProcessing(true);
    try {
      setError('');
      console.log('🔄 Calling updateStudent with is_active: false');
      await apiClient.updateStudent(selectedStudent.id, { is_active: false });
      console.log('✅ Student deactivated successfully');
      
      setSuccess(`🔒 ${selectedStudent.first_name} ${selectedStudent.last_name} başarıyla pasife düşürüldü!`);
      await loadStudents(1, pageSize, filters, false); // isInitialLoad = false
    } catch (error: any) {
      console.error('❌ Error deactivating student:', error);
      if (error.response?.data?.detail) {
        setError(`❌ ${error.response.data.detail}`);
      } else {
        setError(`❌ Öğrenci pasife düşürülemedi. Lütfen tekrar deneyin.`);
      }
    } finally {
      setIsProcessing(false);
      setShowDeactivateDialog(false);
      setSelectedStudent(null);
    }
  };

  const handleActivateConfirm = async () => {
    if (!selectedStudent) return;

    setIsProcessing(true);
    try {
      setError('');
      console.log('🔄 Calling updateStudent with is_active: true');
      await apiClient.updateStudent(selectedStudent.id, { is_active: true });
      console.log('✅ Student activated successfully');
      
      setSuccess(`✅ ${selectedStudent.first_name} ${selectedStudent.last_name} başarıyla aktifleştirildi!`);
      await loadStudents(1, pageSize, filters, false); // isInitialLoad = false
    } catch (error: any) {
      console.error('❌ Error activating student:', error);
      if (error.response?.data?.detail) {
        setError(`❌ ${error.response.data.detail}`);
      } else {
        setError(`❌ Öğrenci aktifleştirilemedi. Lütfen tekrar deneyin.`);
      }
    } finally {
      setIsProcessing(false);
      setShowActivateDialog(false);
      setSelectedStudent(null);
    }
  };


  const handleOpenModal = () => {
    setEditingStudent(null);
    setFormData({ first_name: '', last_name: '', grade: 1 });
    setFormErrors({ first_name: '', last_name: '', grade: '' });
    setError('');
    setSuccess('');
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingStudent(null);
    setFormData({ first_name: '', last_name: '', grade: 1 });
    setFormErrors({ first_name: '', last_name: '', grade: '' });
    setError('');
    setSuccess('');
  };

  // Filter update functions
  const updateFilter = (key: string, value: any) => {
    console.log(`🔍 updateFilter called: ${key} = ${value}`);
    setFilters(prev => {
      const newFilters = {
        ...prev,
        [key]: value
      };
      console.log('🔍 New filters:', newFilters);
      return newFilters;
    });
    setCurrentPage(1);
  };

  // Calculate active filter count
  const calculateActiveFilterCount = useCallback(() => {
    let count = 0;
    
    // Check search
    if (filters.search && filters.search.trim() !== '') count++;
    
    // Check grade
    if (filters.grade !== 'all') count++;
    
    // Check status
    if (filters.status !== 'active') count++;
    
    // Check date range
    if (filters.dateRange.start || filters.dateRange.end) count++;
    
    // Check createdBy
    if (filters.createdBy !== 'all') count++;
    
    // Check sort (only if not default)
    if (filters.sortBy !== 'created_at' || filters.sortOrder !== 'desc') count++;
    
    return count;
  }, [filters]);

  // Update active filter count when filters change
  useEffect(() => {
    setActiveFilterCount(calculateActiveFilterCount());
  }, [filters, calculateActiveFilterCount]);

  const updateDateRange = (key: 'start' | 'end', value: string) => {
    setFilters(prev => ({
      ...prev,
      dateRange: {
        ...prev.dateRange,
        [key]: value
      }
    }));
    setCurrentPage(1);
  };

  // Clear all filters
  const clearFilters = () => {
    const newFilters = {
      search: '',
      grade: 'all' as number | 'all',
      status: 'active' as 'all' | 'active' | 'inactive',
      dateRange: {
        start: '',
        end: ''
      },
      createdBy: 'all' as string | 'all',
      sortBy: 'created_at' as 'created_at' | 'name' | 'grade' | 'status',
      sortOrder: 'desc' as 'asc' | 'desc'
    };
    setFilters(newFilters);
    setCurrentPage(1);
    loadStudents(1, pageSize, newFilters, false); // isInitialLoad = false
  };

  // Count active filters
  useEffect(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.grade !== 'all') count++;
    if (filters.status !== 'active') count++;
    if (filters.dateRange.start || filters.dateRange.end) count++;
    if (filters.createdBy !== 'all') count++;
    setActiveFilterCount(count);
  }, [filters]);

  // Show loading spinner while checking authentication
  if (isAuthLoading) {
    console.log('🔍 StudentsPage: Showing auth loading spinner');
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // If not authenticated, show loading or redirect
  if (!isAuthenticated) {
    if (isAuthLoading) {
      console.log('🔍 StudentsPage: Showing auth loading spinner');
      return (
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Kimlik doğrulanıyor...</p>
          </div>
        </div>
      );
    }
    
    console.log('🔍 StudentsPage: Not authenticated, redirecting to login');
    return null; // Will redirect via useEffect
  }

  console.log('🔍 StudentsPage: Rendering main content');

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className={combineThemeClasses('min-h-screen', themeColors.background.secondary)}>
      <Navigation />

      {/* Content */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="space-y-6">
          {/* Breadcrumbs */}
          <Breadcrumbs />
          
          {/* Header with Add Button */}
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center space-x-2">
                <StudentsIcon size="lg" />
                <span>Öğrenci Yönetimi</span>
              </h1>
              <p className="mt-1 text-sm text-gray-500 flex items-center space-x-2">
                <BookIcon size="sm" />
                <span>Öğrenci bilgilerini kolayca yönetin, ekleyin ve takip edin</span>
              </p>
            </div>
            {hasPermission('student:create') && (
              <ActionTooltip content="Yeni öğrenci eklemek için tıklayın">
                <button
                  onClick={handleOpenModal}
                  className="px-6 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors text-sm flex items-center space-x-2"
                >
                  <AddIcon size="sm" className="text-white" />
                  <span>Öğrenci Ekle</span>
                </button>
              </ActionTooltip>
            )}
          </div>

          {/* Search and Filter Section */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search Input */}
              <div className="md:col-span-2">
                <InfoTooltip content="Öğrenci adı, soyadı veya kayıt numarası ile arama yapabilirsiniz">
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center space-x-2">
                    <SearchIcon size="sm" />
                    <span>Arama</span>
                    {filters.search && (
                      <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                        {students.length} sonuç
                      </span>
                    )}
                  </label>
                </InfoTooltip>
                <form onSubmit={(e) => e.preventDefault()}>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <SearchIcon size="sm" className="text-gray-400" />
                    </div>
                    <input
                      type="text"
                      placeholder="Öğrenci adı, soyadı veya numarası yazın..."
                      value={filters.search}
                      onChange={(e) => updateFilter('search', e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          // No need to call API, filters will be applied automatically
                        }
                      }}
                      className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-slate-700 dark:border-slate-600 dark:text-slate-200 dark:placeholder-slate-400"
                    />
                    {filters.search && (
                      <button
                        type="button"
                        onClick={() => updateFilter('search', '')}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                        title="Aramayı temizle"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                    {tableLoading && (
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
                      </div>
                    )}
                  </div>
                </form>
                {filters.search && (
                  <p className="mt-1 text-xs text-gray-500">
                    💡 Enter tuşuna basarak aramayı hemen başlatabilirsiniz
                  </p>
                )}
              </div>

              {/* Grade Filter */}
              <div>
                <InfoTooltip content="Belirli bir sınıf seviyesindeki öğrencileri filtreleyin">
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center space-x-2">
                    <GradeIcon size="sm" />
                    <span>Sınıf Filtresi</span>
                  </label>
                </InfoTooltip>
                <select
                  value={filters.grade}
                  onChange={(e) => updateFilter('grade', e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value="all">Tüm Sınıflar</option>
                  <option value={1}>1. Sınıf</option>
                  <option value={2}>2. Sınıf</option>
                  <option value={3}>3. Sınıf</option>
                  <option value={4}>4. Sınıf</option>
                  <option value={5}>5. Sınıf</option>
                  <option value={6}>6. Sınıf</option>
                  <option value={0}>Diğer</option>
                </select>
              </div>

              {/* Status Filter */}
              <div>
                <InfoTooltip content="Aktif veya pasif öğrencileri filtreleyin">
                  <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center space-x-2">
                    <FilterIcon size="sm" />
                    <span>Durum Filtresi</span>
                  </label>
                </InfoTooltip>
                <select
                  value={filters.status}
                  onChange={(e) => updateFilter('status', e.target.value)}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value="all">Tüm Durumlar</option>
                  <option value="active">Aktif</option>
                  <option value="inactive">Pasif</option>
                </select>
              </div>
            </div>

            {/* Filter Actions */}
            <div className="mt-4 flex justify-between items-center">
              <div className="text-sm text-gray-500 flex items-center space-x-2">
                <AnalysisIcon size="sm" />
                <span>
                  {filters.search ? (
                    <>
                      <span className="font-medium text-indigo-600">"{filters.search}"</span> için {students.length} sonuç bulundu
                      {totalStudents > students.length && (
                        <span className="text-gray-400"> (toplam {totalStudents} öğrenci)</span>
                      )}
                    </>
                  ) : (
                    `${students.length} öğrenci gösteriliyor (toplam ${totalStudents} öğrenci)`
                  )}
                  {tableLoading && (
                    <span className="ml-2 text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">
                      🔄 Yükleniyor...
                    </span>
                  )}
                </span>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setShowAdvancedFilters(true)}
                  className="px-4 py-2 text-sm text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
                  </svg>
                  <span>Gelişmiş Filtreler</span>
                  {activeFilterCount > 0 && (
                    <span className="bg-blue-500 text-white text-xs rounded-full px-2 py-0.5 min-w-[20px] text-center">
                      {activeFilterCount}
                    </span>
                  )}
                </button>
                <button
                  onClick={clearFilters}
                  className="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors flex items-center space-x-2"
                >
                  <RefreshIcon size="sm" />
                  <span>Filtreleri Temizle</span>
                </button>
              </div>
            </div>
          </div>

          {/* Success/Error Messages */}
          {success && (
            <div className="fixed top-4 right-4 z-50 animate-slide-in">
              <div className="bg-green-500 text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3 min-w-80">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="font-semibold">✅ Başarılı!</p>
                  <p className="text-sm opacity-90">{success}</p>
                </div>
                <button
                  onClick={() => setSuccess('')}
                  className="flex-shrink-0 text-white hover:text-green-200 transition-colors"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="fixed top-4 right-4 z-50 animate-slide-in">
              <div className="bg-red-500 text-white px-6 py-4 rounded-lg shadow-lg flex items-center space-x-3 min-w-80">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <p className="font-semibold">❌ Hata!</p>
                  <p className="text-sm opacity-90">{error}</p>
                </div>
                <button
                  onClick={() => setError('')}
                  className="flex-shrink-0 text-white hover:text-red-200 transition-colors"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          )}

          {/* Students List */}
          {students.length === 0 ? (
            <div className="bg-white shadow rounded-lg p-8 text-center">
              <div className="mb-4">
                {filters.search ? (
                  <SearchIcon size="xl" className="text-indigo-600" />
                ) : (
                  <BookIcon size="xl" className="text-indigo-600" />
                )}
              </div>
              <div className="text-gray-500 text-lg font-medium">
                {filters.search ? (
                  <>
                    <span className="font-medium text-indigo-600">"{filters.search}"</span> için öğrenci bulunamadı
                  </>
                ) : (
                  'Henüz öğrenci bulunmuyor'
                )}
              </div>
              <div className="text-gray-400 text-sm mt-2">
                {filters.search ? (
                  <>
                    💡 <span className="font-medium">"{filters.search}"</span> araması için farklı terimler deneyin
                    <br />
                    Örnek: Ad, soyad veya öğrenci numarası ile arayın
                  </>
                ) : (
                  '✨ İlk öğrencinizi eklemek için yukarıdaki "Öğrenci Ekle" butonuna tıklayın'
                )}
              </div>
              {filters.search && (
                <div className="mt-4 flex justify-center space-x-3">
                  <button
                    onClick={clearFilters}
                    className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors font-medium flex items-center space-x-2"
                  >
                    <RefreshIcon size="sm" />
                    <span>Filtreleri Temizle</span>
                  </button>
                  <button
                    onClick={() => updateFilter('search', '')}
                    className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors font-medium flex items-center space-x-2"
                  >
                    <SearchIcon size="sm" />
                    <span>Aramayı Temizle</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-800 shadow rounded-lg overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-600">
            <h3 className="text-lg font-medium text-gray-900 dark:text-slate-100 flex items-center space-x-2">
              <BookIcon size="sm" />
              <span>Öğrenci Listesi ({students.length})</span>
            </h3>
              </div>
              
              {/* Table */}
              <div className="overflow-x-auto">
                <table className="min-w-full border-collapse">
                  <thead className="bg-gray-50 dark:bg-slate-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-300 uppercase tracking-wider border-b border-gray-200 dark:border-slate-600 w-20">
                        Kayıt No
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-300 uppercase tracking-wider border-b border-gray-200 dark:border-slate-600 min-w-32 max-w-40">
                        Öğrenci Adı Soyadı
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-300 uppercase tracking-wider border-b border-gray-200 dark:border-slate-600 w-24">
                        Sınıf
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-300 uppercase tracking-wider border-b border-gray-200 dark:border-slate-600 w-32">
                        Eklenme Tarihi
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-300 uppercase tracking-wider border-b border-gray-200 dark:border-slate-600 w-32">
                        Kayıt Eden
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-300 uppercase tracking-wider border-b border-gray-200 dark:border-slate-600 w-20">
                        Durum
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-slate-300 uppercase tracking-wider border-b border-gray-200 dark:border-slate-600 w-40">
                        İşlem
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-slate-800">
                    {students.map((student, index) => (
                 <tr 
                   key={student.id} 
                   className={`${hasPermission('student:view') ? 'hover:bg-gray-100 dark:hover:bg-slate-700 cursor-pointer' : 'hover:bg-gray-50 dark:hover:bg-slate-750'} transition-all duration-200 ${index < students.length - 1 ? 'border-b border-gray-200 dark:border-slate-600' : ''}`}
                   onClick={hasPermission('student:view') ? () => router.push(`/students/${student.id}`) : undefined}
                 >
                        <td className="px-4 py-4 text-sm font-medium text-gray-900 dark:text-slate-100 border-r border-gray-100 dark:border-slate-600">
                          #{student.registration_number}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-900 dark:text-slate-100 border-r border-gray-100 dark:border-slate-600">
                          <div className="truncate max-w-48" title={`${student.first_name} ${student.last_name}`}>
                            {student.first_name} {student.last_name}
                          </div>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-500 dark:text-slate-400 border-r border-gray-100 dark:border-slate-600">
                          {student.grade === 0 ? 'Diğer' : `${student.grade}. Sınıf`}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-500 dark:text-slate-400 border-r border-gray-100 dark:border-slate-600">
                          {new Date(student.created_at).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-500 dark:text-slate-400 border-r border-gray-100 dark:border-slate-600">
                          <div className="truncate max-w-32" title={student.created_by}>
                            <UserIcon size="xs" className="inline mr-1" />
                            {student.created_by}
                          </div>
                        </td>
                        <td className="px-4 py-4 border-r border-gray-100 dark:border-slate-600">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            student.is_active 
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' 
                              : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                          }`}>
                            {student.is_active ? 'Aktif' : 'Pasif'}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-sm font-medium">
                          <div className="flex flex-col space-y-1" onClick={(e) => e.stopPropagation()}>
                            {hasPermission('student:view') && (
                              <ActionTooltip content="Öğrenci detaylarını görüntüle">
                                <button
                                  onClick={() => router.push(`/students/${student.id}`)}
                                  className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 text-xs flex items-center space-x-1"
                                >
                                  <ViewIcon size="xs" />
                                  <span>Detay</span>
                                </button>
                              </ActionTooltip>
                            )}
                            {hasPermission('student:update') && (
                              <ActionTooltip content="Öğrenci bilgilerini düzenle">
                                <button
                                  onClick={() => handleEdit(student)}
                                  className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-900 dark:hover:text-indigo-300 text-xs flex items-center space-x-1"
                                >
                                  <EditIcon size="xs" />
                                  <span>Düzenle</span>
                                </button>
                              </ActionTooltip>
                            )}
                            {hasPermission('student:delete') && (
                              student.is_active ? (
                                <ActionTooltip content="Öğrenciyi pasif duruma getir (silmez, sadece gizler)">
                                  <button
                                    onClick={() => handleDelete(student)}
                                    className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 text-xs flex items-center space-x-1"
                                  >
                                    <LockIcon size="xs" />
                                    <span>Pasife Düşür</span>
                                  </button>
                                </ActionTooltip>
                              ) : (
                                <ActionTooltip content="Öğrenciyi aktif duruma getir">
                                  <button
                                    onClick={() => handleActivate(student)}
                                    className="text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300 text-xs flex items-center space-x-1"
                                  >
                                    <UnlockIcon size="xs" />
                                    <span>Aktifleştir</span>
                                  </button>
                                </ActionTooltip>
                              )
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Pagination Controls */}
          {!loading && students.length > 0 && (
            <div className="mt-6 flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
              {/* Page Size Selector */}
              <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700 dark:text-slate-300">
                  Sayfa başına:
                </label>
                <select
                  value={pageSize}
                  onChange={(e) => handlePageSizeChange(parseInt(e.target.value))}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-200"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                
                {/* Custom Page Size Input */}
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    value={customPageSize}
                    onChange={(e) => setCustomPageSize(e.target.value)}
                    placeholder="Özel"
                    min="1"
                    max="100"
                    className="w-16 px-2 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-200"
                  />
                  <button
                    onClick={handleCustomPageSize}
                    disabled={!customPageSize || parseInt(customPageSize) < 1 || parseInt(customPageSize) > 100}
                    className="px-3 py-1 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Uygula
                  </button>
                </div>
              </div>

              {/* Page Info */}
              <div className="text-sm text-gray-700 dark:text-slate-300">
                {totalStudents > 0 ? (
                  <>
                    Sayfa {currentPage} / {totalPages} 
                    <span className="mx-2">•</span>
                    Toplam {totalStudents} öğrenci
                  </>
                ) : (
                  'Öğrenci bulunamadı'
                )}
              </div>

              {/* Page Navigation */}
              <div className="flex items-center space-x-2">
                {/* Previous Button */}
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600"
                >
                  ← Önceki
                </button>

                {/* Page Numbers */}
                <div className="flex space-x-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }

                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`px-3 py-2 text-sm font-medium rounded-md ${
                          currentPage === pageNum
                            ? 'bg-indigo-600 text-white'
                            : 'text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>

                {/* Next Button */}
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                  className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600"
                >
                  Sonraki →
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                {editingStudent ? (
                  <>
                    <EditIcon size="sm" className="inline mr-2" />
                    Öğrenci Düzenle
                  </>
                ) : (
                  <>
                    <AddIcon size="sm" className="inline mr-2" />
                    Yeni Öğrenci Ekle
                  </>
                )}
              </h2>
              <button
                onClick={handleCloseModal}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <span className="text-2xl">×</span>
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {/* First Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <UserIcon size="sm" className="inline mr-1" />
                  Ad <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.first_name}
                  onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                  className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                    formData.first_name.length > 45 ? 'border-orange-300 bg-orange-50' : 
                    formData.first_name.length > 40 ? 'border-yellow-300 bg-yellow-50' : 
                    'border-gray-300'
                  }`}
                  placeholder="Öğrencinin adını girin (örn: Ahmet)"
                  maxLength={50}
                  required
                />
                <div className="flex justify-between items-center mt-1">
                  {formErrors.first_name ? (
                    <div className="text-red-600 text-sm">{formErrors.first_name}</div>
                  ) : (
                    <div className="text-gray-500 text-xs">
                      <LightbulbIcon size="xs" className="inline mr-1" />
                      Ad alanı zorunludur
                    </div>
                  )}
                  <div className={`text-xs ${formData.first_name.length > 45 ? 'text-orange-500' : formData.first_name.length > 40 ? 'text-yellow-500' : 'text-gray-400'}`}>
                    {formData.first_name.length}/50
                  </div>
                </div>
              </div>

              {/* Last Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <UserIcon size="sm" className="inline mr-1" />
                  Soyad <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.last_name}
                  onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                  className={`block w-full px-3 py-2 border rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm ${
                    formData.last_name.length > 45 ? 'border-orange-300 bg-orange-50' : 
                    formData.last_name.length > 40 ? 'border-yellow-300 bg-yellow-50' : 
                    'border-gray-300'
                  }`}
                  placeholder="Öğrencinin soyadını girin (örn: Yılmaz)"
                  maxLength={50}
                  required
                />
                <div className="flex justify-between items-center mt-1">
                  {formErrors.last_name ? (
                    <div className="text-red-600 text-sm">{formErrors.last_name}</div>
                  ) : (
                    <div className="text-gray-500 text-xs">
                      <LightbulbIcon size="xs" className="inline mr-1" />
                      Soyad alanı zorunludur
                    </div>
                  )}
                  <div className={`text-xs ${formData.last_name.length > 45 ? 'text-orange-500' : formData.last_name.length > 40 ? 'text-yellow-500' : 'text-gray-400'}`}>
                    {formData.last_name.length}/50
                  </div>
                </div>
              </div>

              {/* Grade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <GradeIcon size="sm" className="inline mr-1" />
                  Sınıf Seviyesi <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.grade}
                  onChange={(e) => setFormData({ ...formData, grade: parseInt(e.target.value) })}
                  className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                >
                  <option value={1}>1. Sınıf</option>
                  <option value={2}>2. Sınıf</option>
                  <option value={3}>3. Sınıf</option>
                  <option value={4}>4. Sınıf</option>
                  <option value={5}>5. Sınıf</option>
                  <option value={6}>6. Sınıf</option>
                  <option value={0}>Diğer</option>
                </select>
                {formErrors.grade && (
                  <div className="text-red-600 text-sm mt-1">{formErrors.grade}</div>
                )}
              </div>


              {/* Modal Footer */}
              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  className="px-6 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                >
                  ❌ İptal
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSubmitting ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {editingStudent ? 'Güncelleniyor...' : 'Ekleniyor...'}
                    </div>
                  ) : (
                    editingStudent ? '💾 Güncelle' : '➕ Ekle'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Confirmation Dialog */}
      {showEditConfirmDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-slate-100 mb-4">
              {editingStudent ? 'Öğrenci Bilgilerini Güncelle' : 'Yeni Öğrenci Ekle'}
            </h3>
            <p className="text-gray-600 dark:text-slate-300 mb-6">
              {editingStudent 
                ? 'Öğrenci bilgilerini güncellemek istediğinizden emin misiniz? Bu işlem geri alınamaz.'
                : 'Yeni öğrenci eklemek istediğinizden emin misiniz?'
              }
            </p>
            <div className="flex items-center space-x-3">
              <button
                onClick={confirmSubmit}
                disabled={isSubmitting}
                className="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'İşleniyor...' : (editingStudent ? 'Evet, Güncelle' : 'Evet, Ekle')}
              </button>
              <button
                onClick={() => setShowEditConfirmDialog(false)}
                disabled={isSubmitting}
                className="px-4 py-2 bg-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                İptal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Advanced Filters Modal */}
      {showAdvancedFilters && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-slate-600">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                <FilterIcon size="sm" className="mr-2" />
                Gelişmiş Filtreler
              </h2>
              <button
                onClick={() => setShowAdvancedFilters(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <CrossIcon size="sm" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {/* Tarih Aralığı */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <CalendarIcon size="sm" className="inline mr-2" />
                  Kayıt Tarihi Aralığı
                </label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Başlangıç Tarihi</label>
                    <input
                      type="date"
                      value={filters.dateRange.start}
                      onChange={(e) => updateFilter('dateRange', { ...filters.dateRange, start: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-700 dark:text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Bitiş Tarihi</label>
                    <input
                      type="date"
                      value={filters.dateRange.end}
                      onChange={(e) => updateFilter('dateRange', { ...filters.dateRange, end: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-700 dark:text-white"
                    />
                  </div>
                </div>
              </div>

              {/* Sınıf Filtresi */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <GradeIcon size="sm" className="inline mr-2" />
                  Sınıf
                </label>
                <select
                  value={filters.grade}
                  onChange={(e) => updateFilter('grade', e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-700 dark:text-white"
                >
                  <option value="all">Tüm Sınıflar</option>
                  {Array.from({ length: 6 }, (_, i) => i + 1).map(grade => (
                    <option key={grade} value={grade}>{grade}. Sınıf</option>
                  ))}
                  <option value="other">Diğer</option>
                </select>
              </div>

              {/* Durum Filtresi */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <FilterIcon size="sm" className="inline mr-2" />
                  Durum
                </label>
                <select
                  value={filters.status}
                  onChange={(e) => updateFilter('status', e.target.value as 'all' | 'active' | 'inactive')}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-700 dark:text-white"
                >
                  <option value="all">Tüm Durumlar</option>
                  <option value="active">Aktif</option>
                  <option value="inactive">Pasif</option>
                </select>
              </div>

              {/* Sıralama */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <RefreshIcon size="sm" className="inline mr-2" />
                    Sıralama Kriteri
                  </label>
                  <select
                    value={filters.sortBy}
                    onChange={(e) => updateFilter('sortBy', e.target.value as 'created_at' | 'name' | 'grade' | 'status')}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-700 dark:text-white"
                  >
                    <option value="created_at">Kayıt Tarihi</option>
                    <option value="name">Ad Soyad</option>
                    <option value="grade">Sınıf</option>
                    <option value="status">Durum</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    <ClockIcon size="sm" className="inline mr-2" />
                    Sıralama Yönü
                  </label>
                  <select
                    value={filters.sortOrder}
                    onChange={(e) => updateFilter('sortOrder', e.target.value as 'asc' | 'desc')}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-slate-700 dark:text-white"
                  >
                    <option value="desc">Azalan (Yeni → Eski)</option>
                    <option value="asc">Artan (Eski → Yeni)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex justify-between items-center p-6 border-t border-gray-200 dark:border-slate-600">
              <button
                onClick={clearFilters}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-slate-700 rounded-md hover:bg-gray-200 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors flex items-center space-x-2"
              >
                <RefreshIcon size="sm" />
                <span>Tüm Filtreleri Temizle</span>
              </button>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowAdvancedFilters(false)}
                  className="px-6 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-slate-700 rounded-md hover:bg-gray-200 dark:hover:bg-slate-600 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors flex items-center space-x-2"
                >
                  <CrossIcon size="sm" />
                  <span>Kapat</span>
                </button>
                <button
                  onClick={() => setShowAdvancedFilters(false)}
                  className="px-6 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors flex items-center space-x-2"
                >
                  <CheckIcon size="sm" />
                  <span>Filtreleri Uygula</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Dialogs */}
      <DeactivateConfirmationDialog
        isOpen={showDeactivateDialog}
        onClose={() => {
          setShowDeactivateDialog(false);
          setSelectedStudent(null);
        }}
        onConfirm={handleDeactivateConfirm}
        itemName={selectedStudent ? `${selectedStudent.first_name} ${selectedStudent.last_name}` : ''}
        isLoading={isProcessing}
      />

      <ActivateConfirmationDialog
        isOpen={showActivateDialog}
        onClose={() => {
          setShowActivateDialog(false);
          setSelectedStudent(null);
        }}
        onConfirm={handleActivateConfirm}
        itemName={selectedStudent ? `${selectedStudent.first_name} ${selectedStudent.last_name}` : ''}
        isLoading={isProcessing}
      />
    </div>
  );
}
