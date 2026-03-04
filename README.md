# Personal Blog

A personal blog built with [Hexo](https://hexo.io) and the [Butterfly](https://github.com/jerryc127/hexo-theme-butterfly) theme, covering C++ technical notes, job hunting experiences, and life essays.

## Tech Stack

- **Framework**: Hexo 8.x
- **Theme**: Butterfly 5.x
- **Image Storage**: Cloudflare R2 (CDN)

## Custom Scripts

### `scripts/cdn_images.js`

Handles image path resolution for both local development and production deployment.

- **Production**: When the environment variable `CDN_BASE_URL` is set, rewrites all relative image paths in generated HTML to absolute CDN URLs (covers `<img>`, `<link>`, and `background-image`).
- **Local dev**: When `CDN_BASE_URL` is not set, registers a middleware that serves images from `source/_posts/images/` at the `/images/` route, so local preview works without any extra setup.

### `scripts/top_img_priority.js`

Adjusts the banner image priority for post pages.

Butterfly's default priority is `page.top_img > page.cover > theme.default_top_img`. This script changes it to `page.top_img > theme.default_top_img > page.cover`, so the global default banner always takes precedence over per-post cover images unless a post explicitly sets its own `top_img`.

## GitHub Actions

### `sync-images-to-r2.yml`

Automatically syncs images to Cloudflare R2 whenever changes are pushed to `source/_posts/images/`. Uses [rclone](https://rclone.org) under the hood.

**Required secrets:**

| Secret | Description |
|--------|-------------|
| `R2_ACCESS_KEY_ID` | Cloudflare R2 access key ID |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 secret access key |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_BUCKET_NAME` | R2 bucket name |

## Local Development

**Prerequisites**: Node.js >= 14

```bash
# Install dependencies
npm install

# Start local server
npm run server
# Visit http://localhost:4000

# Build
npm run build
```

## Writing

```bash
# Create a new post
hexo new post "Title"
```

Posts live in `source/_posts/`. Images go in `source/_posts/images/<category>/`.
