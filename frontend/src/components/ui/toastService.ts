type ToastType = "success" | "error" | "warning" | "info";

let addToastFn: ((type: ToastType, message: string) => void) | null = null;

export function registerToastHandler(
  handler: ((type: ToastType, message: string) => void) | null,
) {
  addToastFn = handler;
}

export function toast(type: ToastType, message: string) {
  addToastFn?.(type, message);
}
