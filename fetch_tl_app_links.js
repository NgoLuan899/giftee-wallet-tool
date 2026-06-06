const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright-core");

const ROOT = __dirname;
const CHROME_EXE = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PROFILE_DIR = path.join(ROOT, "giftee_chrome_profile");
const G4B_RE = /^https:\/\/g4b\.giftee\.biz\/giftee_boxes\/[0-9a-fA-F-]+/;

function arg(name, fallback = "") {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

function todayTokyo() {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date());
  const m = Object.fromEntries(parts.map((p) => [p.type, p.value]));
  return `${m.year}-${m.month}-${m.day}`;
}

function dateKey(value) {
  const s = String(value || "");
  const m = s.match(/(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  const m2 = s.match(/(\d{2})[/-](\d{2})[/-](\d{4})/);
  if (m2) return `${m2[3]}-${m2[2]}-${m2[1]}`;
  return "";
}

function csv(value) {
  return `"${String(value ?? "").replace(/"/g, '""')}"`;
}

function pickUser(json) {
  if (!json || typeof json !== "object") return null;
  if (json.user && typeof json.user === "object") return json.user;
  if (json.username || json.email || json.points || json.id) return json;
  return null;
}

async function main() {
  const dateMode = arg("date", "today");
  const date = dateMode === "today" ? todayTokyo() : dateMode;
  const output = arg("output", path.join(ROOT, `tl_app_links_${dateMode === "all" ? "all" : date}.txt`));
  const csvOutput = arg("csv", output.replace(/\.txt$/i, ".csv"));

  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    executablePath: CHROME_EXE,
    headless: true,
    viewport: { width: 1280, height: 900 },
  });
  const page = context.pages()[0] || await context.newPage();

  try {
    await page.goto("https://tl-app.pro.vn/", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(1500);

    const me = await page.evaluate(async () => {
      const r = await fetch("/api/auth/me", { credentials: "same-origin" });
      const text = await r.text();
      let json = null;
      try { json = JSON.parse(text); } catch {}
      return { ok: r.ok, status: r.status, json, text };
    });
    if (!me.ok || !pickUser(me.json)) {
      const preview = String(me.text || "").slice(0, 180).replace(/\s+/g, " ");
      throw new Error(`TL-APP chưa login hoặc session hết hạn: /api/auth/me status=${me.status} body=${preview}`);
    }

    const data = await page.evaluate(async () => {
      const r = await fetch("/api/rut-nhanh/history", { credentials: "same-origin" });
      if (!r.ok) throw new Error(`/api/rut-nhanh/history status=${r.status}`);
      return r.json();
    });

    const rows = Array.isArray(data.history) ? data.history : [];
    const filtered = rows.filter((h) => {
      if (dateMode !== "all" && dateKey(h.time) !== date) return false;
      if (String(h.status || "").toLowerCase() !== "success") return false;
      if (!G4B_RE.test(String(h.link || ""))) return false;
      return true;
    });

    const seen = new Set();
    const unique = [];
    for (const h of filtered) {
      if (seen.has(h.link)) continue;
      seen.add(h.link);
      unique.push(h);
    }

    fs.writeFileSync(output, unique.map((h) => h.link).join("\n") + (unique.length ? "\n" : ""), "utf8");
    const headers = ["taskId", "time", "platform", "statusLabel", "amount", "link"];
    fs.writeFileSync(
      csvOutput,
      "\ufeff" + headers.join(",") + "\n" + unique.map((h) => headers.map((k) => csv(h[k])).join(",")).join("\n") + "\n",
      "utf8"
    );

    const totalAmount = unique.reduce((sum, h) => sum + Number(h.amount || 0), 0);
    console.log(`TL_APP_LINKS date=${dateMode === "all" ? "all" : date} count=${unique.length} totalJPY=${totalAmount}`);
    console.log(`TXT=${output}`);
    console.log(`CSV=${csvOutput}`);
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  console.error(error.message || error);
  process.exit(1);
});
