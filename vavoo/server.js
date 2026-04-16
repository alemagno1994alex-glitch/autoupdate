const { Command } = require('commander');
const express = require('express');
const { Readable } = require('node:stream');
const { pipeline } = require('node:stream/promises');
const NodeCache = require('node-cache');

const program = new Command();

program
    .name('vavoo-iptv-stream-proxy')
    .description('Local proxy for Vavoo IPTV streams')
    .option('--http-host <host>', 'Local HTTP host for displayed URLs', '127.0.0.1')
    .option('--http-port <port>', 'Local HTTP port', '8888')
    .option('--vavoo-language <language>', 'Language sent to Vavoo APIs', 'de')
    .option('--vavoo-region <region>', 'Region sent to Vavoo APIs', 'US')
    .option('--vavoo-url-list <selection>', 'URL list to use: primary, fallback, both', 'both')
    .parse(process.argv);

const options = program.opts();

function getBaseSites(selection) {
    const normalized = String(selection || 'both').trim().toLowerCase();
    if (normalized === 'primary') return ['https://vavoo.to'];
    if (normalized === 'fallback') return ['https://kool.to'];
    return ['https://vavoo.to', 'https://kool.to'];
}

const app = express();
const httpHost = options.httpHost;
const port = Number(options.httpPort);
const currentLanguage = options.vavooLanguage;
const currentRegion = options.vavooRegion;
const baseSites = getBaseSites(options.vavooUrlList);

const cache = new NodeCache();
const CHANNELS_CACHE_KEY = 'vavoo_channels';
const SIGNATURE_CACHE_KEY = 'vavoo_addon_sig';
// Per ogni canale, salviamo la base URL del suo stream HLS
const streamBaseCache = new NodeCache({ stdTTL: 300 });

const COUNTRY_SEPARATORS = ['➾', '⟾', '->', '→', '»', '›'];
const PING_URLS = [
    'https://www.lokke.app/api/app/ping',
    'https://www.vavoo.tv/api/app/ping'
];

// ============================================================
// HELPERS
// ============================================================

function getLocalBaseUrl() {
    return `http://${httpHost}:${port}`;
}

function normalize(value) {
    return String(value || '').trim().toLowerCase();
}

function extractCountry(group) {
    const rawGroup = String(group || '').trim();
    if (!rawGroup) return 'default';
    for (const separator of COUNTRY_SEPARATORS) {
        if (rawGroup.includes(separator)) {
            return rawGroup.split(separator)[0].trim() || 'default';
        }
    }
    return rawGroup;
}

function getCatalogHeaders(signature) {
    return {
        'content-type': 'application/json; charset=utf-8',
        'mediahubmx-signature': signature,
        'user-agent': 'MediaHubMX/2',
        'accept': '*/*',
        'Accept-Language': currentLanguage,
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
    };
}

function getPingPayload() {
    const currentTimestamp = Date.now();
    return {
        reason: 'app-focus',
        locale: currentLanguage,
        theme: 'dark',
        metadata: {
            device: { type: 'desktop', uniqueId: `node-${currentTimestamp}` },
            os: { name: 'linux', version: 'Linux', abis: ['x64'], host: 'node' },
            app: { platform: 'electron' },
            version: { package: 'tv.vavoo.app', binary: '3.1.8', js: '3.1.8' }
        },
        appFocusTime: 0, playerActive: false, playDuration: 0,
        devMode: false, hasAddon: true, castConnected: false,
        package: 'tv.vavoo.app', version: '3.1.8', process: 'app',
        firstAppStart: currentTimestamp, lastAppStart: currentTimestamp,
        ipLocation: null, adblockEnabled: true,
        proxy: { supported: ['ss'], engine: 'Mu', enabled: false, autoServer: true },
        iap: { supported: false }
    };
}

async function requestJson(opts) {
    const response = await fetch(opts.url, {
        method: opts.method || 'GET',
        headers: opts.headers,
        body: opts.body ? JSON.stringify(opts.body) : undefined,
        signal: AbortSignal.timeout(opts.timeout || 30000),
    });
    const body = await response.json();
    if (!response.ok) {
        const error = new Error(`HTTP ${response.status} for ${opts.url}`);
        error.statusCode = response.status;
        error.body = body;
        throw error;
    }
    return body;
}

// ============================================================
// VAVOO API
// ============================================================

async function getAddonSignature() {
    const cached = cache.get(SIGNATURE_CACHE_KEY);
    if (cached) return cached;

    const payload = getPingPayload();
    for (const url of PING_URLS) {
        try {
            const body = await requestJson({ method: 'POST', url, body: payload });
            const signature = body?.addonSig;
            if (signature) {
                cache.set(SIGNATURE_CACHE_KEY, signature, 300);
                return signature;
            }
        } catch (error) {
            console.log(`[vavoo] addonSig request failed for ${url}: ${error.message}`);
        }
    }
    throw new Error('Unable to obtain addonSig');
}

function mapCatalogItem(item) {
    return {
        id: String(item?.ids?.id || item?.id || item?.url),
        url: item.url,
        name: item.name || 'Unknown Channel',
        logo: item.logo || '',
        group: item.group || '',
        country: extractCountry(item.group)
    };
}

async function loadCatalogFromBase(baseUrl, signature) {
    const catalogUrl = `${baseUrl.replace(/\/$/, '')}/mediahubmx-catalog.json`;
    const headers = getCatalogHeaders(signature);
    const channels = [];
    let cursor = null;

    while (true) {
        const body = await requestJson({
            method: 'POST',
            url: catalogUrl,
            headers,
            body: {
                language: currentLanguage, region: currentRegion,
                catalogId: 'iptv', id: 'iptv',
                adult: false, search: '', sort: '', filter: {},
                cursor, clientVersion: '3.0.2'
            }
        });
        const items = Array.isArray(body?.items) ? body.items : [];
        for (const item of items) {
            if (item?.type === 'iptv' && item?.url) {
                channels.push(mapCatalogItem(item));
            }
        }
        if (!body?.nextCursor) break;
        cursor = body.nextCursor;
    }
    return channels;
}

async function getChannels(forceRefresh = false) {
    if (forceRefresh) cache.del(CHANNELS_CACHE_KEY);
    const cached = cache.get(CHANNELS_CACHE_KEY);
    if (cached) return cached;

    const signature = await getAddonSignature();
    for (const baseUrl of baseSites) {
        try {
            const channels = await loadCatalogFromBase(baseUrl, signature);
            cache.set(CHANNELS_CACHE_KEY, channels, 300);
            console.log(`[vavoo] channels loaded from ${baseUrl}: ${channels.length}`);
            return channels;
        } catch (error) {
            console.log(`[vavoo] catalog load failed for ${baseUrl}: ${error.message}`);
        }
    }
    throw new Error('Unable to load channel catalog');
}

async function getChannelsByCountry(country) {
    const channels = await getChannels();
    return channels.filter((ch) => normalize(ch.country) === normalize(country));
}

async function getCountries() {
    const channels = await getChannels();
    return [...new Set(
        channels.map((ch) => ch.country).filter((c) => c && normalize(c) !== 'default')
    )].sort((a, b) => a.localeCompare(b));
}

async function findChannelById(id) {
    const channels = await getChannels();
    return channels.find((ch) => String(ch.id) === String(id));
}

async function resolveStreamUrl(channel) {
    const signature = await getAddonSignature();
    for (const baseUrl of baseSites) {
        const resolveUrl = `${baseUrl.replace(/\/$/, '')}/mediahubmx-resolve.json`;
        try {
            const body = await requestJson({
                method: 'POST',
                url: resolveUrl,
                headers: getCatalogHeaders(signature),
                body: {
                    language: currentLanguage, region: currentRegion,
                    url: channel.url, clientVersion: '3.0.2'
                }
            });
            if (Array.isArray(body) && body[0]?.url) return body[0].url;
            if (body?.url) return body.url;
            if (body?.streamUrl) return body.streamUrl;
        } catch (error) {
            console.log(`[vavoo] resolve failed for ${baseUrl}: ${error.message}`);
        }
    }
    throw new Error(`Unable to resolve stream for channel ${channel.name}`);
}

// ============================================================
// HLS MANIFEST REWRITING
// Legge il manifest upstream e riscrive gli URL dei segmenti
// in modo che passino tutti per il nostro proxy
// ============================================================

/**
 * Dato l'URL assoluto di un segmento upstream, lo codifica
 * in un token base64url e restituisce l'URL locale del proxy.
 */
function encodeSegmentUrl(absoluteUrl) {
    const token = Buffer.from(absoluteUrl).toString('base64url');
    return `${getLocalBaseUrl()}/seg/${token}`;
}

/**
 * Risolve un URL di segmento (relativo o assoluto) rispetto
 * alla base URL del manifest.
 */
function resolveSegmentUrl(segmentHref, manifestBaseUrl) {
    if (/^https?:\/\//i.test(segmentHref)) return segmentHref;
    return new URL(segmentHref, manifestBaseUrl).href;
}

/**
 * Scarica il manifest HLS e riscrive tutti i riferimenti
 * (segmenti .ts, chiavi EXT-X-KEY, playlist variante) 
 * in modo che passino per il proxy locale.
 */
async function fetchAndRewriteManifest(manifestUrl) {
    const response = await fetch(manifestUrl, {
        headers: { 'User-Agent': 'VAVOO/2.6' },
        signal: AbortSignal.timeout(15000)
    });
    if (!response.ok) throw new Error(`Manifest fetch failed: HTTP ${response.status}`);

    const text = await response.text();
    // Base URL = tutto fino all'ultimo slash del manifest
    const manifestBase = manifestUrl.replace(/[^/]+$/, '');

    const lines = text.split('\n');
    const rewritten = lines.map((line) => {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) {
            // Gestisci EXT-X-KEY URI= e EXT-X-MAP URI=
            const keyMatch = trimmed.match(/^(#EXT-X-KEY:.*URI=")([^"]+)(".*)/);
            if (keyMatch) {
                const absUrl = resolveSegmentUrl(keyMatch[2], manifestBase);
                return keyMatch[1] + encodeSegmentUrl(absUrl) + keyMatch[3];
            }
            const mapMatch = trimmed.match(/^(#EXT-X-MAP:.*URI=")([^"]+)(".*)/);
            if (mapMatch) {
                const absUrl = resolveSegmentUrl(mapMatch[2], manifestBase);
                return mapMatch[1] + encodeSegmentUrl(absUrl) + mapMatch[3];
            }
            return line;
        }
        // Righe non-commento = URL di segmento o sub-playlist
        const absUrl = resolveSegmentUrl(trimmed, manifestBase);
        if (absUrl.includes('.m3u8')) {
            // Sub-playlist (multi-bitrate): proxia come manifest annidato
            const token = Buffer.from(absUrl).toString('base64url');
            return `${getLocalBaseUrl()}/manifest/${token}`;
        }
        // Segmento media (.ts, .aac, .mp4, ecc.)
        return encodeSegmentUrl(absUrl);
    });

    return rewritten.join('\n');
}

// ============================================================
// PROXY GENERICO PER STREAM BINARIO (usato per i segmenti)
// ============================================================

async function proxyBinary(req, res, upstreamUrl, label) {
    const controller = new AbortController();
    const onClose = () => controller.abort();
    req.on('close', onClose);
    res.on('close', onClose);

    try {
        const upstream = await fetch(upstreamUrl, {
            signal: controller.signal,
            headers: { 'User-Agent': 'VAVOO/2.6', 'Connection': 'close' }
        });

        if (!upstream.ok || !upstream.body) {
            throw new Error(`upstream HTTP ${upstream.status}`);
        }

        const ct = upstream.headers.get('content-type');
        if (ct) res.setHeader('Content-Type', ct);
        const cl = upstream.headers.get('content-length');
        if (cl) res.setHeader('Content-Length', cl);
        const ar = upstream.headers.get('accept-ranges');
        if (ar) res.setHeader('Accept-Ranges', ar);

        const nodeStream = Readable.fromWeb(upstream.body);
        nodeStream.on('error', () => {});
        res.on('error', () => {});

        await pipeline(nodeStream, res);
    } catch (error) {
        if (controller.signal.aborted) return; // client ha chiuso, normale
        console.log(`[proxy] error "${label}": ${error.message}`);
        if (!res.headersSent) res.status(500).send(error.message);
    }
}

// ============================================================
// HOMEPAGE
// ============================================================

function buildHomePage() {
    const baseUrl = getLocalBaseUrl();
    const links = [
        ['Tutti i canali', `${baseUrl}/channels.m3u8`],
        ['Solo Italy', `${baseUrl}/channels.m3u8?country=Italy`],
        ['Solo Germany', `${baseUrl}/channels.m3u8?country=Germany`],
        ['Solo France', `${baseUrl}/channels.m3u8?country=France`],
        ['Solo Spain', `${baseUrl}/channels.m3u8?country=Spain`],
        ['Solo United Kingdom', `${baseUrl}/channels.m3u8?country=United%20Kingdom`],
        ['Lista paesi', `${baseUrl}/countries`],
    ];
    return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Vavoo Proxy</title>
  <style>
    :root { color-scheme: dark; --bg: #111; --text: #f3f3f3; --muted: #b8b8b8; --link: #8fd3ff; }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: sans-serif; background: var(--bg); color: var(--text); }
    main { max-width: 760px; margin: 0 auto; padding: 24px 18px 40px; }
    h1 { margin: 0 0 10px; font-size: 28px; }
    p { margin: 0 0 18px; color: var(--muted); }
    ul { margin: 0; padding-left: 20px; }
    li { margin: 10px 0; }
    a { color: var(--link); word-break: break-all; }
  </style>
</head>
<body>
  <main>
    <h1>Vavoo Proxy</h1>
    <p>Local proxy — HLS manifest rewriting attivo.</p>
    <ul>
      ${links.map(([label, url]) => `<li>${label}: <a href="${url}">${url}</a></li>`).join('\n      ')}
    </ul>
  </main>
</body>
</html>`;
}

// ============================================================
// ROUTES
// ============================================================

// CORS per l'HTML locale
app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', '*');
    next();
});

app.get('/', (req, res) => {
    res.type('html').send(buildHomePage());
});

app.get('/countries', async (req, res) => {
    try {
        res.json(await getCountries());
    } catch (error) {
        console.log('[vavoo] countries error', error.message);
        res.status(500).send(error.message);
    }
});

app.get('/channels.m3u8', async (req, res) => {
    try {
        const country = req.query.country;
        const channels = country ? await getChannelsByCountry(country) : await getChannels();
        const localBase = getLocalBaseUrl();
        const output = ['#EXTM3U'];

        for (const channel of channels) {
            output.push(`#EXTINF:-1 tvg-name="${channel.name}" group-title="${channel.country}" tvg-logo="${channel.logo}" tvg-id="${channel.name}",${channel.name}`);
            output.push('#EXTVLCOPT:http-user-agent=VAVOO/2.6');
            output.push(`${localBase}/stream/${encodeURIComponent(channel.id)}`);
        }

        res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
        res.send(output.join('\n'));
    } catch (error) {
        console.log('[vavoo] channels.m3u8 error', error.message);
        res.status(500).send(error.message);
    }
});

/**
 * Route principale: risolve il canale, scarica il manifest HLS,
 * lo riscrive con URL locali e lo restituisce al client.
 * HLS.js riceverà solo URL del nostro proxy → nessun 404.
 */
app.get('/stream/:id', async (req, res) => {
    const connId = req.socket.remoteAddress;
    const userAgent = req.headers['user-agent'] ?? 'unknown';

    try {
        console.log(`[${connId}] stream request: "${req.params.id}" UA: "${userAgent}"`);

        const channel = await findChannelById(req.params.id);
        if (!channel) {
            return res.status(404).send(`unknown channel: ${req.params.id}`);
        }

        const streamUrl = await resolveStreamUrl(channel);
        console.log(`[${connId}] resolved "${channel.name}": ${streamUrl}`);

        const rewritten = await fetchAndRewriteManifest(streamUrl);
        res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
        res.setHeader('Cache-Control', 'no-cache');
        res.send(rewritten);

    } catch (error) {
        console.log(`[${connId}] playback error`, error.message);
        if (!res.headersSent) res.status(500).send(error.message);
    }
});

/**
 * Route per sub-playlist (manifest annidati multi-bitrate).
 * Il token è l'URL upstream codificato in base64url.
 */
app.get('/manifest/:token', async (req, res) => {
    try {
        const upstreamUrl = Buffer.from(req.params.token, 'base64url').toString('utf8');
        console.log(`[manifest] rewriting: ${upstreamUrl}`);
        const rewritten = await fetchAndRewriteManifest(upstreamUrl);
        res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
        res.setHeader('Cache-Control', 'no-cache');
        res.send(rewritten);
    } catch (error) {
        console.log(`[manifest] error: ${error.message}`);
        if (!res.headersSent) res.status(500).send(error.message);
    }
});

/**
 * Route per segmenti media (.ts, .aac, .mp4, chiavi EXT-X-KEY, ecc.)
 * Il token è l'URL assoluto upstream codificato in base64url.
 */
app.get('/seg/:token', async (req, res) => {
    try {
        const upstreamUrl = Buffer.from(req.params.token, 'base64url').toString('utf8');
        await proxyBinary(req, res, upstreamUrl, upstreamUrl.split('/').pop());
    } catch (error) {
        console.log(`[seg] error: ${error.message}`);
        if (!res.headersSent) res.status(500).send(error.message);
    }
});

// ============================================================
// START
// ============================================================

app.listen(port, httpHost, () => {
    const baseUrl = getLocalBaseUrl();
    console.log(`\n✓ Vavoo Proxy listening on ${baseUrl}/`);
    console.log(`  M3U:              ${baseUrl}/channels.m3u8`);
    console.log(`  Filtrato Italy:   ${baseUrl}/channels.m3u8?country=Italy`);
    console.log(`  Lista paesi:      ${baseUrl}/countries\n`);
});
