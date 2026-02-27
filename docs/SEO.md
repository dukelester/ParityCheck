# SEO Setup for ParityCheck

This document describes the SEO optimizations in place and how to customize them for your deployment.

## What's Included

### Meta Tags (`frontend/index.html`)
- **Title**: Optimized for search with primary keywords (environment drift, dev/staging/prod parity)
- **Description**: 150–160 character meta description for search snippets
- **Keywords**: environment drift, dev prod parity, configuration drift, env vars diff, dependency tracking, devops, CI/CD, envguard
- **Robots**: `index, follow` to allow crawling
- **Canonical URL**: Prevents duplicate content issues

### Open Graph & Twitter Cards
- Rich previews when sharing links on social media
- `og:image` / `twitter:image`: Add `public/og-image.png` (1200×630px recommended) for best compatibility. An SVG fallback is provided.

### JSON-LD Structured Data
- `SoftwareApplication` schema for rich search results
- Helps search engines understand the product (category, features, free tier)

### Crawler Files
- **`public/robots.txt`**: Allows all crawlers, points to sitemap
- **`public/sitemap.xml`**: Lists main pages (/, /docs, /login, /signup)

### Semantic HTML
- `<main>`, `<section>`, proper heading hierarchy (h1 → h2 → h3)
- `aria-labelledby` for screen readers and crawlers

## Customizing for Your Domain

If you deploy to a different domain (e.g. `https://your-domain.com`):

1. **Update `frontend/index.html`**: Replace `https://paritycheck.dev` in:
   - `link rel="canonical"`
   - `og:url`, `og:image`
   - `twitter:url`, `twitter:image`

2. **Update `frontend/public/robots.txt`**: Change the Sitemap URL

3. **Update `frontend/public/sitemap.xml`**: Replace all `https://paritycheck.dev` URLs

4. **Add an OG image** (optional but recommended): Create `public/og-image.png` at 1200×630px for social sharing. The SVG fallback works but PNG/JPEG has broader support.

## Submitting to Search Engines

- **Google**: [Google Search Console](https://search.google.com/search-console) — add your site and submit the sitemap
- **Bing**: [Bing Webmaster Tools](https://www.bing.com/webmasters) — submit sitemap
- **Other**: Most engines discover via sitemap and links

## Search-Friendly Keywords

The landing page and meta tags target queries like:
- environment drift detection
- dev staging production parity
- configuration drift tool
- env vars diff
- "it works on my machine" solution
- dependency tracking across environments
