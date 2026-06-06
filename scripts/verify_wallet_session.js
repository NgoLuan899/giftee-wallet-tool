const path = require("path");
const { chromium } = require("playwright-core");

const ROOT = path.resolve(__dirname, "..");
const CHROME_EXE = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

function arg(name, fallback = "") {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const PROFILE_DIR = arg("profile", path.join(ROOT, "giftee_chrome_profile"));

function hasLoginText(text) {
  return /ログイン|メールアドレス|パスワード|Sign in|Login/i.test(text || "");
}

(async () => {
  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    executablePath: CHROME_EXE,
    headless: true,
    viewport: { width: 1280, height: 900 },
  });
  const page = context.pages()[0] || await context.newPage();
  try {
    await page.goto("https://wallet.vaton.jp/home", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    await page.waitForTimeout(2500);
    const url = page.url();
    const text = await page.locator("body").innerText({ timeout: 5000 }).catch(() => "");
    const loggedIn = url.includes("wallet.vaton.jp") && !hasLoginText(text) && /home|point|gift|wallet/i.test(url + "\n" + text);
    console.log(JSON.stringify({
      loggedIn,
      url,
      note: loggedIn ? "LOGGED_IN" : "NOT_LOGGED_IN",
    }));
  } finally {
    await context.close();
  }
})().catch((error) => {
  console.log(JSON.stringify({
    loggedIn: false,
    url: "",
    note: "ERROR",
    error: String(error.message || error),
  }));
  process.exit(0);
});
