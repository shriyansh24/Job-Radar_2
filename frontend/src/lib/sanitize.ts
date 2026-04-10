import DOMPurify, { type Config } from "dompurify";

const RESUME_PREVIEW_SANITIZE_CONFIG: Config = {
  ADD_ATTR: ["class"],
};

function escapeStyleBlock(styleText: string): string {
  return styleText.replace(/<\/style/gi, "<\\/style");
}

export function sanitizeHtml(html: string | null | undefined): string {
  if (!html) {
    return "";
  }

  const document = new DOMParser().parseFromString(html, "text/html");
  const preservedHeadStyles = Array.from(document.head.querySelectorAll("style"))
    .map((styleElement) => styleElement.textContent?.trim() ?? "")
    .filter(Boolean)
    .map((styleText) => `<style>${escapeStyleBlock(styleText)}</style>`)
    .join("");

  const sanitizedBody = DOMPurify.sanitize(
    document.body.innerHTML || html,
    RESUME_PREVIEW_SANITIZE_CONFIG
  );

  return `${preservedHeadStyles}${sanitizedBody}`;
}
