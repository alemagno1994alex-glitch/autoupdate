const https = require('https');
const { URL } = require('url');

exports.handler = async (event) => {
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'GET,HEAD,OPTIONS',
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 204, headers: cors, body: '' };
  }

  const target = event.queryStringParameters?.url;
  if (!target?.startsWith('http')) {
    return { statusCode: 400, headers: cors, body: 'URL non valido' };
  }

  try {
    const parsed = new URL(target);
    const result = await new Promise((resolve, reject) => {
      const req = https.request({
        hostname: parsed.hostname,
        path: parsed.pathname + parsed.search,
        method: 'GET',
        headers: {
          'Referer': 'https://vixsrc.to/',
          'Origin': 'https://vixsrc.to',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
        }
      }, (res) => {
        const chunks = [];
        res.on('data', c => chunks.push(c));
        res.on('end', () => resolve({
          statusCode: res.statusCode,
          headers: { ...cors, 'content-type': res.headers['content-type'] || '' },
          body: Buffer.concat(chunks).toString('base64'),
          isBase64Encoded: true,
        }));
      });
      req.on('error', reject);
      req.end();
    });
    return result;
  } catch (e) {
    return { statusCode: 502, headers: cors, body: e.message };
  }
};