const fs = require("fs");
const path = require("path");
const readline = require("readline");
const { chromium } = require("playwright-core");

const ROOT = path.resolve(__dirname, "..");
const CHROME_EXE = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const PROFILE_DIR = path.join(ROOT, "giftee_chrome_profile");
const URL_CODE_RE = /giftee_boxes\/([0-9a-fA-F-]+)/;

function arg(name, fallback = "") {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

function hasFlag(name) {
  return process.argv.includes(`--${name}`);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function ask(message) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => rl.question(message, () => {
    rl.close();
    resolve();
  }));
}

function readLinks(file) {
  return [...new Set(
    fs.readFileSync(file, "utf8")
      .split(/\r?\n/)
      .map((x) => x.trim())
      .filter(Boolean)
  )];
}

function csv(value) {
  return `"${String(value ?? "").replace(/"/g, '""')}"`;
}

function appendCsv(file, row) {
  const headers = ["index", "url", "status", "point", "initialPoint", "giftWalletPointMerged", "finalUrl", "note", "time"];
  if (!fs.existsSync(file)) fs.writeFileSync(file, "\ufeff" + headers.join(",") + "\n", "utf8");
  fs.appendFileSync(file, headers.map((h) => csv(row[h])).join(",") + "\n", "utf8");
}

function urlCode(link) {
  const match = link.match(URL_CODE_RE);
  return match ? match[1] : "";
}

async function checkGiftee(link) {
  const code = urlCode(link);
  if (!code) return { status: "INVALID_LINK", point: "", initialPoint: "", giftWalletPointMerged: "" };

  const boxQuery = `query GetGifteeBox($urlCode: String!) {
    gifteeBox(urlCode: $urlCode) {
      initialPoint
      point
      expiredAt
    }
  }`;
  const giftsQuery = `query GetGifteeBoxGifts($urlCode: String!) {
    gifteeBox(urlCode: $urlCode) {
      giftWalletPointMerged
      gifts { url exchangedAt }
    }
  }`;
  async function gql(query, operationName) {
    const res = await fetch("https://g4b.giftee.biz/public_api/graphql", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "accept": "application/json",
        "origin": "https://g4b.giftee.biz",
        "referer": link,
      },
      body: JSON.stringify({ operationName, variables: { urlCode: code }, query }),
    });
    const json = await res.json();
    if (json.errors) throw new Error(json.errors.map((e) => e.message).join("; "));
    return json.data.gifteeBox;
  }
  const box = await gql(boxQuery, "GetGifteeBox");
  const gifts = await gql(giftsQuery, "GetGifteeBoxGifts");
  const point = Number(box.point || 0);
  const merged = gifts.giftWalletPointMerged === true;
  return {
    status: merged ? "DA_NAP" : point > 0 ? "CHUA_NAP" : "HET_POINT_KHONG_RO",
    point,
    initialPoint: box.initialPoint,
    giftWalletPointMerged: merged,
  };
}

function directUrl(link) {
  return `https://wallet.vaton.jp/gifts/new?gift_url=${encodeURIComponent(link)}&gift_origin=g4b&referer=giftee_box&convert_to_point=true`;
}

async function waitAfterDirect(page, timeout = 15000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    const url = page.url();
    if (url.includes("/home") || url.includes("/point/charge")) return url;
    await sleep(500);
  }
  return page.url();
}

async function main() {
  const input = arg("input", path.join(ROOT, "pending_giftee_links.txt"));
  const output = arg("output", path.join(ROOT, "wallet_merge_results.csv"));
  const start = Number(arg("start", "1"));
  const limit = Number(arg("limit", "1"));
  const waitMs = Number(arg("wait", "6500"));
  const gapMs = Number(arg("gap", "3000"));
  const noPrompt = hasFlag("no-prompt");

  let links = readLinks(input).slice(start - 1);
  if (limit > 0) links = links.slice(0, limit);

  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    executablePath: CHROME_EXE,
    headless: false,
    viewport: null,
    args: ["--start-maximized"],
  });
  const page = context.pages()[0] || await context.newPage();

  await page.goto("https://wallet.vaton.jp/", { waitUntil: "domcontentloaded" });
  console.log("Chrome profile:", PROFILE_DIR);
  console.log("Login/check wallet first. Gift links are not opened yet.");
  if (noPrompt) {
    console.log("No-prompt mode: starting direct merge immediately.");
  } else {
    await ask("Login xong / sẵn sàng thì bấm Enter để bắt đầu direct merge...");
  }

  for (let i = 0; i < links.length; i++) {
    const index = start + i;
    const link = links[i];
    console.log(`[${index}] ${link}`);
    let row = { index, url: link, finalUrl: "", note: "", time: new Date().toISOString() };
    try {
      const before = await checkGiftee(link);
      if (before.status === "DA_NAP") {
        row = { ...row, ...before, finalUrl: "", note: "already merged before attempt" };
      } else {
        await page.goto(directUrl(link), { waitUntil: "domcontentloaded", timeout: 45000 });
        row.finalUrl = await waitAfterDirect(page, 20000);
        await sleep(waitMs);
        const after = await checkGiftee(link);
        row = { ...row, ...after, note: after.status === "DA_NAP" ? "merged by direct url" : "still not merged after direct url" };
      }
    } catch (error) {
      row.status = "ERROR";
      row.note = String(error.message || error).slice(0, 500);
    }
    appendCsv(output, row);
    console.log(` -> ${row.status} point=${row.point} merged=${row.giftWalletPointMerged} ${row.note}`);
    if (row.status === "ERROR") break;
    await sleep(gapMs + Math.floor(Math.random() * Math.max(1, gapMs)));
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
