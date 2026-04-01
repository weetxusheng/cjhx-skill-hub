import { expect, test } from "@playwright/test";

test("portal categories page loads with database-backed state", async ({ page }) => {
  await page.goto("http://127.0.0.1:4173");
  await expect(page.getByRole("heading", { name: "创金严选-技能广场", exact: true })).toBeVisible();
  await expect(page.getByText("探索全部技能")).toBeVisible();
});

test("portal site nav scrolls to the matching section", async ({ page }) => {
  await page.goto("http://127.0.0.1:4173/categories");

  await page.getByRole("link", { name: "平台概览" }).click();
  await expect(page).toHaveURL(/#overview-section$/);
  await expect(page.locator("#overview-section")).toBeInViewport();

  await page.getByRole("link", { name: "技能广场" }).click();
  await expect(page).toHaveURL(/#marketplace-section$/);
  await expect(page.locator("#marketplace-section")).toBeInViewport();
});

test("portal upload entry stays on the portal and opens upload center", async ({ page }) => {
  await page.goto("http://127.0.0.1:4173/categories");

  await page.getByRole("button", { name: "登录收藏" }).click();
  const loginDialog = page.getByRole("dialog", { name: "登录后继续" });
  await loginDialog.getByLabel("用户名").fill("admin");
  await loginDialog.getByLabel("密码").fill("ChangeMe123!");
  await loginDialog.getByRole("button", { name: /登\s*录/ }).click();

  await expect(page.getByRole("button", { name: "我要上传" })).toBeVisible();
  await page.getByRole("button", { name: "我要上传" }).click();

  await expect(page.getByRole("dialog", { name: "前台上传中心" })).toBeVisible();
  await expect(page.getByText("拖拽 ZIP 到这里")).toBeVisible();
  await expect(page.getByText("我的上传记录")).toBeVisible();
});

test("portal upload center shows admin contacts for users without upload permission", async ({ page, request }) => {
  const seededUserLogin = await request.post("http://127.0.0.1:8000/api/auth/login", {
    data: { username: "fixture_observer", password: "Pass123!" },
  });
  test.skip(seededUserLogin.status() !== 200, "requires local workbench seed user fixture_observer");

  await page.goto("http://127.0.0.1:4173/categories");

  await page.getByRole("button", { name: "登录收藏" }).click();
  const loginDialog = page.getByRole("dialog", { name: "登录后继续" });
  await loginDialog.getByLabel("用户名").fill("fixture_observer");
  await loginDialog.getByLabel("密码").fill("Pass123!");
  await loginDialog.getByRole("button", { name: /登\s*录/ }).click();

  await expect(page.getByRole("button", { name: "进入上传通道" })).toBeVisible();
  await page.getByRole("button", { name: "进入上传通道" }).click();

  const forbiddenBlock = page.locator("#portal-upload-center-forbidden");
  await expect(page.getByRole("dialog", { name: "前台上传中心" })).toBeVisible();
  await expect(forbiddenBlock).toContainText("当前账号还没有投稿权限");
  await expect(forbiddenBlock).toContainText("当前可联系的管理员");
  await expect(forbiddenBlock).toContainText("管理员");
});

test("portal interactive submissions show explicit success feedback", async ({ page }) => {
  await page.goto("http://127.0.0.1:4173/categories");

  await page.getByRole("button", { name: "登录收藏" }).click();
  const loginDialog = page.getByRole("dialog", { name: "登录后继续" });
  await loginDialog.getByLabel("用户名").fill("admin");
  await loginDialog.getByLabel("密码").fill("ChangeMe123!");
  await loginDialog.getByRole("button", { name: /登\s*录/ }).click();

  await page.getByRole("button", { name: "查看详情" }).first().click();
  await expect(page.getByText("README")).toBeVisible();

  const favoriteButton = page.locator("#portal-skill-detail-favorite-button");
  const originalLabel = (await favoriteButton.textContent())?.trim() ?? "";
  await favoriteButton.click();
  await expect(page.locator(".ant-message")).toContainText(originalLabel.includes("取消收藏") ? "已取消收藏" : "已加入收藏");
});
