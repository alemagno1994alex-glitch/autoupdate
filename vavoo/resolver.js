import express from "express";
import fetch from "node-fetch";

const app = express();
const PORT = 8888;

// Cache in RAM
let addonSigCache = null;
let catalogCache = null;
let lastSigFetch = 0;
let lastCatalogFetch = 0;

async function getAddonSig() {
  const now = Date.now();
  if (addonSigCache && now - lastSigFetch < 300000) return addonSigCache;

  const payload = {
    reason: "app-focus",
    locale: "de",
    metadata: { device: { type: "desktop" } }
  };

  const urls = [
    "https://www.lokke.app/api/app/ping",
    "https://www.vavoo.tv/api/app/ping"
  ];

  for (const u of urls) {
    try {
      const r = await fetch(u, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload)
      });

      const body = await r.json();
      if (body?.addonSig) {
        addonSigCache = body.addonSig;
        lastSigFetch = now;
        return addonSigCache;
      }
    } catch (e) {}
  }

  throw new Error("Unable to obtain addonSig");
}

function extractCountry(group) {
  if (!group) return "default";
  const separators = ["➾", "⟾", "->", "→", "»", "›"];
  for (const sep of separators) {
    if (group.includes(sep)) return group.split(sep)[0].trim();
  }
  return group.trim();
}

async function loadCatalog() {
  const now = Date.now();
  if (catalogCache && now - lastCatalogFetch < 300000) return catalogCache;

  const signature = await getAddonSig();
  const bases = ["https://vavoo.to", "https://kool.to"];
  let channels = [];

  for (const base of bases) {
    try {
      const r = await fetch(base + "/mediahubmx-catalog.json", {
        method: "POST",
        headers: {
          "mediahubmx-signature": signature,
          "user-agent": "MediaHubMX/2",
          "accept-language": "de",
          "content-type": "application/json"
        },
        body: JSON.stringify({
          language: "de",
          region: "US",
          catalogId: "iptv",
          id: "iptv"
        })
      });

      const body = await r.json();
      if (!body?.items) continue;

      channels = body.items
        .filter(i => i.type === "iptv" && i.url)
        .map(i => ({
          id: i.ids?.id || i.id || i.url,
          url: i.url,
          name: i.name,
          logo: i.logo || "",
          group: i.group || "",
          country: extractCountry(i.group)
        }));

      if (channels.length > 0) break;
    } catch (e) {}
  }

  catalogCache = channels;
  lastCatalogFetch = now;
  return channels;
}

async function resolveStream(channel) {
  const signature = await getAddonSig();
  const bases = ["https://vavoo.to", "https://kool.to"];

  for (const base of bases) {
    try {
      const r = await fetch(base + "/mediahubmx-resolve.json", {
        method: "POST",
        headers: {
          "mediahubmx-signature": signature,
          "user-agent": "MediaHubMX/2",
          "content-type": "application/json"
        },
        body: JSON.stringify({
          language: "de",
          region: "US",
          url: channel.url
        })
      });

      const body = await r.json();

      if (Array.isArray(body) && body[0]?.url) return body[0].url;
      if (body?.url) return body.url;
      if (body?.streamUrl) return body.streamUrl;
    } catch (e) {}
  }

  throw new Error("Unable to resolve stream");
}

// ---------------------------
// ROUTES
// ---------------------------

app.get("/countries", async (req, res) => {
  const catalog = await loadCatalog();
  const countries = [...new Set(catalog.map(c => c.country))]
    .filter(c => c !== "default")
    .sort();
  res.json(countries);
});

app.get("/channels", async (req, res) => {
  const country = req.query.country;
  const catalog = await loadCatalog();

  const filtered = country
    ? catalog.filter(c => c.country.toLowerCase() === country.toLowerCase())
    : catalog;

  res.json(filtered);
});

app.get("/resolve/:id", async (req, res) => {
  const id = req.params.id;
  const catalog = await loadCatalog();
  const channel = catalog.find(c => c.id == id);

  if (!channel) return res.status(404).json({ error: "Unknown channel" });

  const url = await resolveStream(channel);

  res.json({ stream: url });
});

app.listen(PORT, () => {
  console.log("Resolver running on port", PORT);
});
