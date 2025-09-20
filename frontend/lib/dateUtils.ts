/**
 * Date utility functions for handling timezone conversions
 */

/**
 * Converts a date string to Turkish timezone if it doesn't already have timezone info
 * @param dateString - The date string to convert
 * @returns Date string with Turkish timezone (+03:00)
 */
export function toTurkishTime(dateString: string): string {
  if (!dateString) return '';
  
  // If the date string already has timezone info, return as is
  if (dateString.includes('+') || dateString.includes('Z')) {
    return dateString;
  }
  
  // Add Turkish timezone if not present
  return dateString + '+03:00';
}

/**
 * Formats a date string for display in Turkish locale
 * @param dateString - The date string to format
 * @param options - Intl.DateTimeFormatOptions
 * @returns Formatted date string
 */
export function formatTurkishDate(
  dateString: string, 
  options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }
): string {
  if (!dateString) return '';
  
  const turkishTime = toTurkishTime(dateString);
  return new Date(turkishTime).toLocaleString('tr-TR', options);
}

/**
 * Formats a date string for display as date only in Turkish locale
 * @param dateString - The date string to format
 * @returns Formatted date string
 */
export function formatTurkishDateOnly(dateString: string): string {
  return formatTurkishDate(dateString, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

