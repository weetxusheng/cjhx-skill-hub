import { expect, test } from "@playwright/test";

test("admin can log in and visit governance pages", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("http://127.0.0.1:4174/login");
  await page.getByLabel("用户名").fill("admin");
  await page.getByLabel("密码").fill("ChangeMe123!");
  await page.getByRole("button", { name: /登\s*录/ }).click();
  await page.waitForURL(/127\.0\.0\.1:4174\/(?!login).*/, { timeout: 15000 });
  await expect(page.locator(".admin-sider")).toBeVisible({ timeout: 30000 });
  await page.getByRole("link", { name: "审核中心" }).first().click();
  await expect(page.locator("#admin-reviews-table-card")).toBeVisible();
  await page.getByRole("link", { name: "待发布" }).first().click();
  await expect(page.locator("#admin-releases-table-card")).toBeVisible();
  await page.getByRole("link", { name: "处理记录" }).first().click();
  await expect(page.locator("#admin-review-history-table-card")).toBeVisible();
  await page.getByRole("link", { name: "分类管理" }).first().click();
  await expect(page.locator("#admin-categories-table-card")).toBeVisible();
  await page.getByRole("link", { name: "用户管理" }).first().click();
  await expect(page.locator("#admin-users-table-card")).toBeVisible();
  await page.getByRole("link", { name: "角色管理" }).first().click();
  await expect(page.locator("#admin-roles-table-card")).toBeVisible();
  await page.getByRole("link", { name: "审计日志" }).first().click();
  await expect(page.locator("#admin-audit-logs-table-card")).toBeVisible();
});

test("admin high-risk governance actions require confirmation before submit", async ({ page }) => {
  await page.addInitScript(() => window.localStorage.clear());
  await page.goto("http://127.0.0.1:4174/login");
  await page.getByLabel("用户名").fill("admin");
  await page.getByLabel("密码").fill("ChangeMe123!");
  await page.getByRole("button", { name: /登\s*录/ }).click();
  await page.waitForURL(/127\.0\.0\.1:4174\/(?!login).*/, { timeout: 15000 });

  await page.getByRole("link", { name: "用户管理" }).first().click();
  await expect(page.locator("#admin-users-table-card")).toBeVisible();
  await page.getByRole("button", { name: /禁\s*用/ }).first().click();
  await expect(page.getByText("禁用用户")).toBeVisible();
  await page.getByRole("button", { name: /Cancel|取消/ }).click();

  await page.getByRole("link", { name: "角色管理" }).first().click();
  await expect(page.locator("#admin-roles-table-card")).toBeVisible();
  await page.getByRole("button", { name: /停\s*用/ }).first().click();
  await expect(page.getByText("停用角色")).toBeVisible();
});
