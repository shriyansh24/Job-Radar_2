import { expect, test } from "@playwright/test";

import {
  buildTestUser,
  expectShellChrome,
  loginThroughUi,
  registerTestUser,
} from "../support/auth";

test.describe("smoke/auth-shell", () => {
  test("logs in through the UI and lands in the authenticated shell", async ({
    page,
    request,
  }) => {
    const user = buildTestUser("shell");

    await registerTestUser(request, user);
    await loginThroughUi(page, user);
    await expectShellChrome(page);
    await page.getByRole("button", { name: /logout/i }).click();
    await expect(page).toHaveURL(/\/login$/);
  });
});
