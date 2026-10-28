import { expect, test, type Page } from "@playwright/test";

const PHOTO = "https://lh3.googleusercontent.com/a/asha-photo";
// A one-pixel PNG, so the "good photo" case needs no network.
const PIXEL = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
  "base64",
);

async function signInWithPhoto(page: Page) {
  await page.route("**/api/auth/session", (route) =>
    route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        user: { id: "google-1", name: "Asha Buyer", email: "asha@example.com", image: PHOTO },
        expires: "2999-01-01T00:00:00.000Z",
      }),
    }),
  );
}

test("a photo that fails to load is replaced by the person's initials", async ({ page }) => {
  await signInWithPhoto(page);
  await page.route(PHOTO, (route) => route.fulfill({ status: 404, body: "" }));
  await page.goto("/");

  const avatar = page.getByRole("button", { name: "Account menu" });
  await expect(avatar).toHaveText("AB");
  await expect(avatar.locator("img")).toHaveCount(0);
});

test("a photo that loads is shown with the alt text Account menu and no referrer", async ({ page }) => {
  await signInWithPhoto(page);
  await page.route(PHOTO, (route) => route.fulfill({ contentType: "image/png", body: PIXEL }));
  await page.goto("/");

  const photo = page.getByRole("button", { name: "Account menu" }).locator("img");
  await expect(photo).toHaveAttribute("src", PHOTO);
  await expect(photo).toHaveAttribute("alt", "Account menu");
  await expect(photo).toHaveAttribute("referrerpolicy", "no-referrer");
});

test("the content security policy lets Google pictures load", async ({ request }) => {
  const response = await request.get("/");
  const policy = response.headers()["content-security-policy"] ?? "";
  expect(policy).toContain("img-src 'self' data: blob: https://lh3.googleusercontent.com");
});
