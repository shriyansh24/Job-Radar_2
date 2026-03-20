import "@testing-library/jest-dom/vitest";

const storage = (() => {
  let store = new Map<string, string>();
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, String(value));
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => {
      store = new Map<string, string>();
    },
  };
})();

if (
  typeof window !== "undefined" &&
  (!window.localStorage ||
    typeof window.localStorage.getItem !== "function" ||
    typeof window.localStorage.setItem !== "function" ||
    typeof window.localStorage.removeItem !== "function")
) {
  Object.defineProperty(window, "localStorage", {
    value: storage,
    configurable: true,
  });
}
