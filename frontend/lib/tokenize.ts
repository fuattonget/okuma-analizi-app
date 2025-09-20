// Turkish tokenization function - preserves apostrophes, removes punctuation
export function tokenize_tr(text: string): string[] {
  // Keep original casing and extract words only (no punctuation)
  // This pattern matches Turkish words including çğıöşüâîû characters and apostrophes
  // but excludes punctuation marks like .,!?;: " " , etc.
  // Includes all apostrophe-like characters: ' ' ` ` ´ ´
  const tokens = text.match(/[a-zA-ZçğıöşüâîûÇĞIİÖŞÜÂÎÛ''`´]+/g) || [];
  
  // Filter out empty strings and very short words (1 char) unless they are common
  const commonSingleChars = new Set(['a', 'e', 'i', 'ı', 'o', 'ö', 'u', 'ü']);
  const filteredTokens = tokens.filter(token => 
    token.length > 1 || commonSingleChars.has(token)
  );
  
  return filteredTokens;
}

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


