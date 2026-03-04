# Personal Blog

A personal blog built with [Hexo](https://hexo.io) and the [Butterfly](https://github.com/jerryc127/hexo-theme-butterfly) theme, covering C++ technical notes, job hunting experiences, and life essays.

## Tech Stack

- **Framework**: Hexo 8.x
- **Theme**: Butterfly 5.x
- **Hosting**: [Cloudflare Pages](https://pages.cloudflare.com)
- **Image Storage**: [Cloudflare R2](https://developers.cloudflare.com/r2/) (CDN)

## Features

### Dev/Prod Parity

The local development environment mirrors production exactly. A custom Hexo script detects whether `CDN_BASE_URL` is set — in production it rewrites image paths to CDN URLs; locally it spins up a middleware serving the same images from `source/_posts/images/`. No environment-specific configuration needed to get started.

### Image Auto-Sync

Images are stored in `source/_posts/images/` and served via Cloudflare R2 CDN in production. Any push to `source/_posts/images/` triggers a GitHub Action that syncs changed images to R2 using [rclone](https://rclone.org) — no manual upload needed.

**Required secrets for the GitHub Action:**

| Secret | Description |
|--------|-------------|
| `R2_ACCESS_KEY_ID` | Cloudflare R2 access key ID |
| `R2_SECRET_ACCESS_KEY` | Cloudflare R2 secret access key |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_BUCKET_NAME` | R2 bucket name |

### Continuous Deployment

Every push to the `main` branch automatically triggers a build and deployment via Cloudflare Pages. No manual deployment steps required — the live site is always in sync with the repository.

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
