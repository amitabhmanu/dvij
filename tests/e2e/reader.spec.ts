import { expect, test } from "@playwright/test";

type Page = import("@playwright/test").Page;
const status = (page: Page) => page.locator(".reader [aria-live]");

/** Open a reader URL and wait until the island has hydrated (controls live). */
async function open(page: Page, url: string) {
  await page.goto(url);
  await page.locator('.reader[data-hydrated="true"]').waitFor();
}

/** How far the art runs under the Text sidebar, in px; 0 when it sits clear. */
function artUnderText(page: Page) {
  return page.evaluate(() => {
    const text = document.querySelector(".reader .transcript")!.getBoundingClientRect();
    const art = [...document.querySelectorAll(".reader .page-frame, .reader .panel-focus")]
      .map((el) => el.getBoundingClientRect())
      .filter((r) => r.width > 0);
    return Math.max(0, ...art.map((r) => Math.round(r.right - text.left)));
  });
}

test("deep link opens the requested page", async ({ page }) => {
  await open(page, "/read/b1/7");
  await expect(page.locator(".reader .pages img").first()).toHaveAttribute("src", /b1-p00[67]-/);
  await expect(status(page)).toContainText(/Pages? .*7/);
});

test("arrow keys turn pages and update the URL", async ({ page, isMobile }) => {
  test.skip(isMobile, "keyboard navigation is a desktop feature");
  await open(page, "/read/b1/2");
  await page.locator(".reader .stage").focus();
  await page.keyboard.press("ArrowRight");
  await expect(page).toHaveURL(/\/read\/b1\/4$/); // spread 2-3 -> 4-5
  await page.keyboard.press("ArrowLeft");
  await expect(page).toHaveURL(/\/read\/b1\/2$/);
});

test("wide screens show two-page spreads", async ({ page, isMobile }) => {
  test.skip(isMobile, "desktop only");
  await open(page, "/read/b1/4");
  await expect(page.locator(".reader .pages img")).toHaveCount(2);
  await expect(status(page)).toContainText("Pages 4–5");
});

test("phones show single pages and panel mode steps through panels", async ({ page, isMobile }) => {
  test.skip(!isMobile, "phone only");
  await open(page, "/read/b1/4");
  await expect(page.locator(".reader .pages img")).toHaveCount(1);
  await page.getByRole("button", { name: "Panels" }).click();
  await expect(page).toHaveURL(/#p1$/);
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page).toHaveURL(/#p2$/);
  await expect(status(page)).toContainText("panel 2 of");
});

test("the Text sidebar sits beside the art, not over it", async ({ page, isMobile }) => {
  test.skip(isMobile, "desktop only");
  // 1280 is where it was worst: the sidebar hid 47% of a spread's right-hand page
  await page.setViewportSize({ width: 1280, height: 800 });
  await open(page, "/read/b2/6");
  await expect(page.locator(".reader .pages img")).toHaveCount(2);
  await page.getByRole("button", { name: "Text", exact: true }).click();
  await expect.poll(() => artUnderText(page)).toBe(0);
  // panel mode sizes itself from the stage too, so it moves over as well
  await page.getByRole("button", { name: "Panels", exact: true }).click();
  await expect.poll(() => artUnderText(page)).toBe(0);
  // and closing the text gives the art its width back
  await page.getByRole("button", { name: "Spread", exact: true }).click();
  await page.getByRole("button", { name: "Text", exact: true }).click();
  await expect(page.locator(".reader .stage")).toHaveCSS("padding-right", "0px");
});

test("on a phone, Text stays an overlay with no gutter", async ({ page, isMobile }) => {
  test.skip(!isMobile, "phone only");
  await open(page, "/read/b3/10");
  await page.getByRole("button", { name: "Text", exact: true }).click();
  await expect(page.locator(".reader .transcript")).toBeVisible();
  await expect(page.locator(".reader .stage")).toHaveCSS("padding-right", "0px");
});

test("panel deep link opens panel mode", async ({ page }) => {
  await open(page, "/read/b1/4#p3");
  await expect(status(page)).toContainText("panel 3 of");
});

test("reading progress survives a reload", async ({ page }) => {
  await open(page, "/read/b1/9");
  await expect(status(page)).toContainText("9");
  await page.goto("/read/");
  await expect(page.locator('.book-card[data-book="b1"] .actions .btn')).toHaveText("Continue");
  await page.goto("/");
  await expect(page.locator("#start")).toHaveText("Continue reading");
});

test("chapter links land on the chapter's first page", async ({ page }) => {
  await page.goto("/read/b1/ch/1");
  await expect(page).toHaveURL(/\/read\/b1\/4/);
});

test("search finds dialogue", async ({ page }) => {
  await page.goto("/search/");
  await page.locator("#search input").fill("driving too long");
  await expect(page.locator(".pagefind-ui__result-link").first()).toHaveAttribute("href", /\/read\/b1\/2\/?$/);
});

test("end of a book offers the next one", async ({ page }) => {
  await open(page, "/read/b1/42");
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByRole("link", { name: /Continue to Book 2/ })).toBeVisible();
});
