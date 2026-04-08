import DOMPurify from 'dompurify';

/**
 * Sanitizes an HTML string to prevent XSS attacks while allowing safe tags and attributes.
 * Useful for rendering content with dangerouslySetInnerHTML.
 *
 * @param html - The raw HTML string to sanitize.
 * @returns The sanitized HTML string.
 */
export function sanitizeHtml(html: string | null | undefined): string {
  if (!html) return '';

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'p', 'a', 'ul', 'ol',
      'li', 'b', 'i', 'strong', 'em', 'strike', 'code', 'hr', 'br', 'div',
      'table', 'thead', 'caption', 'tbody', 'tr', 'th', 'td', 'pre', 'span', 'style', 'section', 'header', 'footer'
    ],
    ALLOWED_ATTR: ['href', 'name', 'target', 'class', 'style', 'id'],
    FORCE_BODY: true,
  }) as string;
}
