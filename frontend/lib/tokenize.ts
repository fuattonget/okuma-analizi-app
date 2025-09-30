
// Split text into tokens and separators
export function tokenizeWithSeparators(text: string): Array<{type: 'word' | 'separator', content: string}> {
  const result: Array<{type: 'word' | 'separator', content: string}> = [];
  let current = '';
  
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const isWordChar = /[a-zA-Zçğıöşüâîû]/i.test(char);
    
    if (isWordChar) {
      current += char;
    } else {
      if (current) {
        result.push({ type: 'word', content: current });
        current = '';
      }
      result.push({ type: 'separator', content: char });
    }
  }
  
  if (current) {
    result.push({ type: 'word', content: current });
  }
  
  return result;
}
