import { expect, test } from "@playwright/test";

test("portal categories page loads with database-backed state", async ({ page }) => {
  await page.goto("http://127.0.0.1:4173");
  await expect(page.getByRole("heading", { name: "自由探索，创金技能广场" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "技能广场", exact: true })).toBeVisible();
});
