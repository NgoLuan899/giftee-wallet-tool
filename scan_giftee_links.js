const fs = require("fs");
const path = require("path");

const INPUT = process.argv[2] || path.join(__dirname, "input_giftee_links.txt");
const OUT_CSV = process.argv[3] || path.join(__dirname, "giftee_scan_results.csv");
const OUT_LEFT = process.argv[4] || path.join(__dirname, "pending_giftee_links.txt");
const URL_CODE_RE = /giftee_boxes\/([0-9a-fA-F-]+)/;

const boxQuery = `query GetGifteeBox($urlCode: String!) {
  gifteeBox(urlCode: $urlCode) {
    urlCode
    initialPoint
    point
    expiredAt
    unsealed
    giftWalletStorable
    giftWalletPointMergeable
    contentSelectionsPageVisible
  }
}`;

const giftsQuery = `query GetGifteeBoxGifts($urlCode: String!) {
  gifteeBox(urlCode: $urlCode) {
    giftWalletPointMerged
    gifts {
      url
      exchangedAt
      expiresAt
      content {
        name
        brand { name }
      }
    }
  }
}`;

function csv(value) {
  return `"${String(value ?? "").replace(/"/g, '""')}"`;
}

function readLinks(file) {
  const links = fs
    .readFileSync(file, "utf8")
    .split(/\r?\n/)
    .map((x) => x.trim())
    .filter(Boolean);
  return [...new Set(links)];
}

function urlCode(link) {
  const match = link.match(URL_CODE_RE);
  return match ? match[1] : "";
}

async function graphql(query, code) {
  const response = await fetch("https://g4b.giftee.biz/public_api/graphql", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "accept": "application/json",
      "origin": "https://g4b.giftee.biz",
      "referer": `https://g4b.giftee.biz/giftee_boxes/${code}`,
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
    },
    body: JSON.stringify({
      operationName: query.includes("GetGifteeBoxGifts") ? "GetGifteeBoxGifts" : "GetGifteeBox",
      variables: { urlCode: code },
      query,
    }),
  });

  const text = await response.text();
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${text.slice(0, 200)}`);
  }
  const json = JSON.parse(text);
  if (json.errors && json.errors.length) {
    throw new Error(json.errors.map((e) => e.message).join("; "));
  }
  return json.data.gifteeBox;
}

function classify(box, giftsBox) {
  const point = Number(box.point || 0);
  const initialPoint = Number(box.initialPoint || 0);
  const merged = giftsBox.giftWalletPointMerged === true;
  const giftCount = Array.isArray(giftsBox.gifts) ? giftsBox.gifts.length : 0;
  const expired = box.expiredAt && new Date(box.expiredAt).getTime() < Date.now();

  if (expired && point > 0 && !merged) return "HET_HAN_CON_POINT";
  if (merged) return "DA_NAP";
  if (point > 0) return "CHUA_NAP";
  if (giftCount > 0) return "DA_DOI_GIFT";
  if (initialPoint > 0 && point === 0) return "HET_POINT_KHONG_RO";
  return "KHONG_RO";
}

async function checkOne(link, index, total) {
  const code = urlCode(link);
  if (!code) {
    return { status: "INVALID_LINK", point: "", initialPoint: "", expiredAt: "", unsealed: "", giftWalletPointMerged: "", giftCount: "", link };
  }

  const box = await graphql(boxQuery, code);
  const giftsBox = await graphql(giftsQuery, code);
  const status = classify(box, giftsBox);
  const giftCount = Array.isArray(giftsBox.gifts) ? giftsBox.gifts.length : 0;
  process.stdout.write(`[${index}/${total}] ${status} point=${box.point} initial=${box.initialPoint}\n`);
  return {
    status,
    point: box.point,
    initialPoint: box.initialPoint,
    expiredAt: box.expiredAt,
    unsealed: box.unsealed,
    giftWalletPointMerged: giftsBox.giftWalletPointMerged,
    giftCount,
    giftWalletPointMergeable: box.giftWalletPointMergeable,
    link,
  };
}

async function main() {
  const links = readLinks(INPUT);
  const rows = [];
  console.log(`Checking ${links.length} links from ${INPUT}`);

  for (let i = 0; i < links.length; i++) {
    const link = links[i];
    try {
      rows.push(await checkOne(link, i + 1, links.length));
    } catch (error) {
      rows.push({
        status: "ERROR",
        point: "",
        initialPoint: "",
        expiredAt: "",
        unsealed: "",
        giftWalletPointMerged: "",
        giftCount: "",
        giftWalletPointMergeable: "",
        link,
        error: String(error.message || error).slice(0, 500),
      });
      process.stdout.write(`[${i + 1}/${links.length}] ERROR ${String(error.message || error).slice(0, 120)}\n`);
    }
    await new Promise((r) => setTimeout(r, 250));
  }

  const headers = [
    "status",
    "point",
    "initialPoint",
    "expiredAt",
    "unsealed",
    "giftWalletPointMerged",
    "giftCount",
    "giftWalletPointMergeable",
    "link",
    "error",
  ];
  fs.writeFileSync(
    OUT_CSV,
    "\ufeff" + headers.join(",") + "\n" + rows.map((row) => headers.map((h) => csv(row[h])).join(",")).join("\n") + "\n",
    "utf8"
  );

  const left = rows.filter((row) => row.status === "CHUA_NAP" || row.status === "HET_HAN_CON_POINT");
  fs.writeFileSync(OUT_LEFT, left.map((row) => row.link).join("\n") + (left.length ? "\n" : ""), "utf8");

  const summary = rows.reduce((acc, row) => {
    acc[row.status] = acc[row.status] || { count: 0, point: 0, initialPoint: 0 };
    acc[row.status].count += 1;
    acc[row.status].point += Number(row.point || 0);
    acc[row.status].initialPoint += Number(row.initialPoint || 0);
    return acc;
  }, {});

  console.log("\nSummary:");
  for (const [status, data] of Object.entries(summary)) {
    console.log(`${status}: count=${data.count}, point=${data.point}, initialPoint=${data.initialPoint}`);
  }
  console.log(`\nCSV: ${OUT_CSV}`);
  console.log(`Left links: ${OUT_LEFT}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
