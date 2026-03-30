import { expect, type APIRequestContext, type Page } from "@playwright/test";
import { randomUUID } from "node:crypto";

const EMAIL_PREFIX = "codex-e2e";
const PASSWORD = "SecurePassword123!";

export type E2ETestUser = {
  email: string;
  password: string;
  displayName: string;
};

export function buildTestUser(suffix = "smoke"): E2ETestUser {
  const stamp = randomUUID().slice(0, 8);
  return {
    email: `${EMAIL_PREFIX}-${suffix}-${stamp}@example.com`,
    password: PASSWORD,
    displayName: `Codex E2E ${suffix}`,
  };
}

export async function registerTestUser(
  request: APIRequestContext,
  user: E2ETestUser
): Promise<void> {
  const response = await request.post("/api/v1/auth/register", {
    data: {
      email: user.email,
      password: user.password,
      display_name: user.displayName,
    },
  });

  expect(response.ok(), `register status ${response.status()}`).toBeTruthy();
  expect(response.status()).toBe(201);
}

export async function loginThroughUi(page: Page, user: E2ETestUser): Promise<void> {
  await page.goto("/login");
  await expect(page.getByRole("heading", { name: /sign in/i })).toBeVisible();
  await page.getByLabel(/email address/i).fill(user.email);
  await page.getByLabel(/password/i).fill(user.password);
  await page.getByRole("button", { name: /^sign in$/i }).click();
  await expect(page).toHaveURL(/\/$/);
}

export async function expectShellChrome(page: Page): Promise<void> {
  await expect(page.getByRole("button", { name: /logout/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /toggle color mode/i })).toBeVisible();
  await expect(page.getByRole("button", { name: /collapse navigation/i })).toBeVisible();
  await expect(page.locator("aside")).toBeVisible();
  await expect(page.getByRole("banner").getByRole("heading", { name: "JobRadar" })).toBeVisible();
  await expect(page.getByRole("complementary").getByRole("heading", { name: "JobRadar" })).toBeVisible();
}
