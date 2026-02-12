/**
 * Hexo filter: replace relative image paths with CDN absolute paths.
 * In local dev mode, serves images from source/_posts/images/ via middleware.
 */

'use strict';

const path = require('path');
const fs = require('fs');

const CDN_BASE_URL = process.env.CDN_BASE_URL;

if (CDN_BASE_URL) {
  const baseUrl = CDN_BASE_URL.replace(/\/+$/, '');

  // Deploy mode: rewrite img src to CDN URLs
  hexo.extend.filter.register('after_render:html', (str) => {
    // Replace <img> src attributes
    str = str.replace(
      /(<img\s[^>]*src=["'])(?:\/\.\/|\.\/|\/)?images\//g,
      `$1${baseUrl}/images/`
    );

    // Replace <link> href attributes (e.g. favicon)
    str = str.replace(
      /(<link\s[^>]*href=["'])(?:\/\.\/|\.\/|\/)?images\//g,
      `$1${baseUrl}/images/`
    );

    // Replace background-image url() paths
    str = str.replace(
      /(url\(["']?)(?:\/\.\/|\.\/|\/)?images\//g,
      `$1${baseUrl}/images/`
    );

    return str;
  });

  hexo.log.info(`[CDN Images] Enabled, base URL: ${baseUrl}`);
} else {
  // Local dev mode: serve /images/ from source/_posts/images/
  hexo.extend.filter.register('server_middleware', (app) => {
    app.use('/images/', (req, res, next) => {
      const filePath = path.join(hexo.source_dir, '_posts', 'images', req.url);

      if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
        res.setHeader('Content-Type', getMimeType(filePath));
        fs.createReadStream(filePath).pipe(res);
      } else {
        next();
      }
    });
  });

  hexo.log.info('[CDN Images] CDN_BASE_URL not set, local image middleware enabled');
}

/** Return MIME type for a given file path. */
function getMimeType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const mimeTypes = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    '.ico': 'image/x-icon',
    '.bmp': 'image/bmp',
  };
  return mimeTypes[ext] || 'application/octet-stream';
}
