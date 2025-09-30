/**
 * Date utility functions for handling timezone conversions
 */

/**
 * Converts a date string to Turkish timezone
 * @param dateString - The date string to convert (assumed to be UTC)
 * @returns Date string with Turkish timezone (+03:00)
 */
export function toTurkishTime(dateString: string): string {
  if (!dateString) return '';
  
  // Parse the date and convert to Turkish timezone
  const date = new Date(dateString);
  
  // Convert to Turkish timezone by adding 3 hours
  const turkishTime = new Date(date.getTime() + (3 * 60 * 60 * 1000));
  
  return turkishTime.toISOString().replace('Z', '+03:00');
}

/**
 * Converts a date string to Turkish timezone and returns a Date object
 * @param dateString - The date string to convert
 * @returns Date object with Turkish timezone
 */
export function toTurkishDate(dateString: string): Date {
  if (!dateString) return new Date();
  
  const turkishTime = toTurkishTime(dateString);
  return new Date(turkishTime);
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
    minute: '2-digit',
    timeZone: 'Europe/Istanbul'
  }
): string {
  if (!dateString) return '';
  
  const turkishTime = toTurkishTime(dateString);
  const date = new Date(turkishTime);
  
  // Ensure we're using Turkish timezone
  return date.toLocaleString('tr-TR', {
    ...options,
    timeZone: 'Europe/Istanbul'
  });
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

/**
 * Formats a date string for display with time only in Turkish locale
 * @param dateString - The date string to format
 * @returns Formatted time string
 */
export function formatTurkishTimeOnly(dateString: string): string {
  return formatTurkishDate(dateString, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'Europe/Istanbul'
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
    second: '2-digit',
    timeZone: 'Europe/Istanbul'
  });
}

