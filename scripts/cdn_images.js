/**
 * Hexo filter: replace relative image paths with CDN absolute paths.
 * Configured via CDN_BASE_URL env variable.
 */

'use strict';

const CDN_BASE_URL = process.env.CDN_BASE_URL;

if (CDN_BASE_URL) {
  const baseUrl = CDN_BASE_URL.replace(/\/+$/, '');

  // Replace img src paths like /images/*, /./images/*, ./images/*
  hexo.extend.filter.register('after_render:html', (str, data) => {
    return str.replace(
      /(<img\s[^>]*src=["'])(?:\/\.\/|\.\/|\/)?images\//g,
      `$1${baseUrl}/images/`
    );
  });

  hexo.log.info(`[CDN Images] Enabled, base URL: ${baseUrl}`);
} else {
  hexo.log.info('[CDN Images] CDN_BASE_URL not set, skipping image path replacement');
}
