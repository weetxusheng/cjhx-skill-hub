import { expect, test } from "@playwright/test";

test("admin can log in and visit governance pages", async ({ page }) => {
  await page.goto("http://127.0.0.1:4174/login");
  await page.getByLabel("用户名").fill("admin");
  await page.getByLabel("密码").fill("ChangeMe123!");
  await page.getByRole("button", { name: /登\s*录/ }).click();
  await expect(page.getByText("Skill Hub 生产化收口中")).toBeVisible();
  await expect(page.getByRole("heading", { name: "工作台" })).toBeVisible();
  await page.getByRole("link", { name: "审核中心" }).click();
  await expect(page.getByRole("heading", { name: "审核中心" })).toBeVisible();
  await page.getByRole("link", { name: "待发布" }).click();
  await expect(page.getByRole("heading", { name: "待发布" })).toBeVisible();
  await page.getByRole("link", { name: "处理记录" }).click();
  await expect(page.getByRole("heading", { name: "处理记录" })).toBeVisible();
  await page.getByRole("link", { name: "分类管理" }).click();
  await expect(page.getByRole("heading", { name: "分类管理" })).toBeVisible();
  await page.getByRole("link", { name: "用户管理" }).click();
  await expect(page.getByRole("heading", { name: "用户管理" })).toBeVisible();
  await page.getByRole("link", { name: "角色管理" }).click();
  await expect(page.getByRole("heading", { name: "角色管理" })).toBeVisible();
  await page.getByRole("link", { name: "审计日志" }).click();
  await expect(page.getByRole("heading", { name: "审计日志" })).toBeVisible();
});
