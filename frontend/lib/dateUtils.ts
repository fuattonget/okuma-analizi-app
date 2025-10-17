/**
 * Date utility functions for handling timezone conversions
 * 
 * Backend sends all dates in UTC format (ISO 8601).
 * Frontend converts UTC to Turkish timezone (UTC+3) for display.
 */

/**
 * Formats a date string for display in Turkish locale
 * Converts UTC time from backend to Turkish timezone (UTC+3)
 * @param dateString - The UTC date string from backend (ISO 8601 format)
 * @param options - Intl.DateTimeFormatOptions for formatting
 * @returns Formatted date string in Turkish locale and timezone
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
  
  // Parse UTC date and convert to Turkish timezone (+3 hours)
  const date = new Date(dateString);
  const turkishDate = new Date(date.getTime() + (3 * 60 * 60 * 1000));
  
  // Format in Turkish locale
  return turkishDate.toLocaleString('tr-TR', options);
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

/**
 * Formats a date string for display with time only in Turkish locale
 * @param dateString - The date string to format
 * @returns Formatted time string
 */
export function formatTurkishTimeOnly(dateString: string): string {
  return formatTurkishDate(dateString, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

/**
 * Formats a date string for display with full date and time in Turkish locale
 * @param dateString - The date string to format
 * @returns Formatted date and time string
 */
export function formatTurkishDateTime(dateString: string): string {
  return formatTurkishDate(dateString, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

/**
 * USAGE GUIDE:
 * 
 * All date functions in this file follow the same pattern:
 * 1. Backend sends UTC dates in ISO 8601 format: "2025-10-17T08:42:00"
 * 2. Frontend adds +3 hours to convert to Turkish timezone
 * 3. Result is formatted in Turkish locale (tr-TR)
 * 
 * Examples:
 * - formatTurkishDate("2025-10-17T08:42:00") → "17 Ekim 2025 11:42"
 * - formatTurkishDateOnly("2025-10-17T08:42:00") → "17 Ekim 2025"
 * - formatTurkishTimeOnly("2025-10-17T08:42:00") → "11:42:00"
 * - formatTurkishDateTime("2025-10-17T08:42:00") → "17 Ekim 2025 11:42:00"
 * 
 * IMPORTANT: Always use these functions for displaying dates from the API.
 * Never use new Date().toLocaleString() directly without timezone conversion.
 */
