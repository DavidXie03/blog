# Personal Blog

A personal blog built with [Hexo](https://hexo.io) and the [Butterfly](https://github.com/jerryc127/hexo-theme-butterfly) theme, covering C++ technical notes, job hunting experiences, and life essays.

## Tech Stack

- **Framework**: Hexo 8.x
- **Theme**: Butterfly 5.x
- **Hosting**: Cloudflare Pages
- **Image Storage**: Cloudflare R2 (CDN)

## Continuous Deployment

Every push to the `main` branch automatically triggers a build and deployment via [Cloudflare Pages](https://pages.cloudflare.com). No manual deployment steps required — the live site is always in sync with the repository.

## Image CDN with Auto-Sync

Images are stored in `source/_posts/images/` and served via Cloudflare R2 CDN in production.

- **Auto-sync**: Any push to `source/_posts/images/` triggers a GitHub Action that syncs changed images to R2 using [rclone](https://rclone.org) — no manual upload needed.
- **CDN rewriting**: A custom Hexo script rewrites all image paths in generated HTML to CDN URLs when `CDN_BASE_URL` is set.
- **Local dev**: When `CDN_BASE_URL` is not set, images are served locally from `source/_posts/images/` via a dev middleware — no configuration needed.

**Required secrets for the GitHub Action:**

| Secret | Description |
|--------|-------------|
| `R2_ACCESS_KEY_ID` | Cloudflare R2 access key ID |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 secret access key |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_BUCKET_NAME` | R2 bucket name |

## Banner Behavior

By default, Butterfly uses post cover images as the page banner. A custom script overrides this priority so the global default banner always takes effect unless a post explicitly sets its own `top_img`. This keeps the visual style consistent across all pages.

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
