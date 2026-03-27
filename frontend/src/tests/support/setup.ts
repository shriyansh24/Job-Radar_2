import "@testing-library/jest-dom/vitest";

const createStorage = () => {
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
};

if (typeof window !== "undefined") {
  const localStorageMock = createStorage();
  const sessionStorageMock = createStorage();

  // Override the runtime web storage shims in tests so setup never touches
  // the host-provided getter that emits `--localstorage-file` warnings.
  Object.defineProperty(window, "localStorage", {
    value: localStorageMock,
    configurable: true,
  });
  Object.defineProperty(window, "sessionStorage", {
    value: sessionStorageMock,
    configurable: true,
  });
  Object.defineProperty(globalThis, "localStorage", {
    value: localStorageMock,
    configurable: true,
  });
  Object.defineProperty(globalThis, "sessionStorage", {
    value: sessionStorageMock,
    configurable: true,
  });
}
