import { chromium } from "playwright";

const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));

await page.goto("http://localhost:5173/login", { waitUntil: "networkidle" });
await page.fill("#username", "admin");
await page.fill("#password", "change_me");
await page.click('button:has-text("Sign in")');
await page.waitForURL("http://localhost:5173/", { timeout: 10000 });
await page.waitForSelector("text=Countries tracked", { timeout: 10000 });
await page.screenshot({ path: "_verify_dashboard.png", fullPage: true });

await page.click('text=GDP');
await page.waitForURL("**/data/gdp");
await page.waitForSelector("text=No results");
await page.screenshot({ path: "_verify_gdp.png", fullPage: true });

console.log(JSON.stringify({ finalUrl: page.url(), errors }, null, 2));
await browser.close();
