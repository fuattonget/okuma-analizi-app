/**
 * Date utility functions for handling timezone conversions
 */

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
    minute: '2-digit',
    timeZone: 'Europe/Istanbul'
  }
): string {
  if (!dateString) return '';
  
  // Backend sends dates in Turkish timezone (+03:00), but JavaScript interprets them as UTC
  // So we need to explicitly set the timezone to Europe/Istanbul
  return new Date(dateString).toLocaleString('tr-TR', options);
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
    day: 'numeric',
    timeZone: 'Europe/Istanbul'
  });
}

