import { readable } from 'svelte/store';
import textContent from './text.yaml';

// Format text with variables
function formatText(text, variables = {}) {
  return text.replace(/\{(\w+)\}/g, (_, key) => 
    variables[key] !== undefined ? variables[key] : `{${key}}`
  );
}

// Create a readable store with the text content
export const text = readable(textContent);

// Helper function to get text with variable replacement
export function getText(path, variables = {}) {
  // Split the path by dots
  const keys = path.split('.');
  
  // Traverse the text object to get the desired string
  let value = textContent;
  for (const key of keys) {
    if (value && value[key] !== undefined) {
      value = value[key];
    } else {
      console.warn(`Text key not found: ${path}`);
      return path; // Return the path if the key is not found
    }
  }
  
  // Format the string if it's a string, otherwise return as is
  if (typeof value === 'string') {
    return formatText(value, variables);
  }
  
  return value;
}
