const path = require("path");
const { chromium } = require("playwright-core");

const ROOT = path.resolve(__dirname, "..");
const CHROME_EXE = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";

function arg(name, fallback = "") {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

function pickUser(json) {
  if (!json || typeof json !== "object") return null;
  if (json.user && typeof json.user === "object") return json.user;
  if (json.username || json.email || json.points || json.id) return json;
  return null;
}

const PROFILE_DIR = arg("profile", path.join(ROOT, "giftee_chrome_profile"));

(async () => {
  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    executablePath: CHROME_EXE,
    headless: true,
    viewport: { width: 1280, height: 900 },
  });
  const page = context.pages()[0] || await context.newPage();
  try {
    await page.goto("https://tl-app.pro.vn/", {
      waitUntil: "domcontentloaded",
      timeout: 30000,
    });
    await page.waitForTimeout(1500);
    const result = await page.evaluate(async () => {
      const r = await fetch("/api/auth/me", { credentials: "same-origin" });
      const text = await r.text();
      let json = null;
      try { json = JSON.parse(text); } catch {}
      return { ok: r.ok, status: r.status, json, text };
    });
    const user = result.ok ? pickUser(result.json) : null;
    const loggedIn = !!user;
    console.log(JSON.stringify({
      loggedIn: !!loggedIn,
      url: page.url(),
      note: loggedIn ? "LOGGED_IN" : "NOT_LOGGED_IN",
      status: result.status,
      username: loggedIn ? user.username : "",
      points: loggedIn ? user.points : "",
      responseKeys: result.json && typeof result.json === "object" ? Object.keys(result.json).slice(0, 12) : [],
      textPreview: loggedIn ? "" : String(result.text || "").slice(0, 220),
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
