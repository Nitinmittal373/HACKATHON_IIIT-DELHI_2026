import { expect, test } from "@playwright/test";

test("the Hindi toggle is remembered and reaches server-rendered pages", async ({ page, context }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Know your builder");

  await page.getByRole("button", { name: "हिं" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("बुक करने से पहले");
  await expect(page.locator("html")).toHaveAttribute("lang", "hi");

  const cookies = await context.cookies();
  expect(cookies.find((cookie) => cookie.name === "neevcheck-lang")?.value).toBe("hi");

  // The confirm screen is rendered on the server, from the cookie.
  await page.goto("/check?q=Supertech%20Eco%20Village");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("2 प्रोजेक्ट मिले");
  await expect(page.getByRole("button", { name: "हाँ, इस प्रोजेक्ट को जाँचें" })).toBeVisible();

  await page.getByRole("button", { name: "EN" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("We found 2 projects");
});
