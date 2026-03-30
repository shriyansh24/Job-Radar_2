import { expect, test } from "@playwright/test";

import { buildTestUser, loginThroughUi, registerTestUser } from "../support/auth";

const ROUTE_EXPECTATIONS = [
  { path: "/", title: "Command Center" },
  { path: "/jobs", title: "Jobs" },
  { path: "/pipeline", title: "Pipeline" },
  { path: "/settings", title: "Settings" },
];

test.describe("flows/route-shell-navigation", () => {
  test("keeps the shell mounted across primary authenticated routes", async ({
    page,
    request,
  }) => {
    const user = buildTestUser("route-nav");

    await registerTestUser(request, user);
    await loginThroughUi(page, user);

    for (const route of ROUTE_EXPECTATIONS) {
      await page.goto(route.path);
      await expect(page).toHaveURL(new RegExp(`${route.path === "/" ? "/$" : route.path}$`));
      await expect(page.locator("aside")).toBeVisible();
      await expect(page.getByRole("button", { name: /logout/i })).toBeVisible();
      await expect(
        page.getByRole("main").getByRole("heading", {
          name: route.title,
          exact: true,
        })
      ).toBeVisible();
    }
  });
});
