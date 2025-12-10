// src/utils/markdown.ts

export const renderMarkdown = (text: string): string => {
  let html = text
    // Horizontal rules
    .replace(/\*\*\*(.*?)\*\*\*/g, '<hr class="my-4 border-slate-300"/>')
    // Bold text
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
    // Italic text
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Headers
    .replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold mt-6 mb-4">$1</h1>')
    .replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold mt-5 mb-3">$1</h2>')
    .replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold mt-4 mb-2">$1</h3>')
    // Line breaks
    .replace(/\n/g, '<br/>');
  
  return html;
};

export const downloadMarkdown = (content: string, filename: string): void => {
  const blob = new Blob([content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
};

export const formatFileName = (noteNumber: string, companyName?: string): string => {
  const timestamp = Date.now();
  const prefix = companyName ? `${companyName}_` : '';
  return `${prefix}note_${noteNumber}_${timestamp}.md`;
};
