---
layout: page
title: Documentation Setup
permalink: /docs/setup/
---

# GitHub Pages Documentation Setup

This document explains how the Argorator documentation site is configured using GitHub Pages and Jekyll.

## Site Structure

```
.
├── _config.yml                    # Jekyll configuration
├── Gemfile                        # Ruby dependencies for local development
├── index.md                       # Main landing page
├── docs/                          # Documentation content
│   ├── README.md                  # Documentation home
│   └── features/                  # Feature-specific documentation
│       └── google_style_annotations.md
├── CHANGELOG.md                   # Version history
└── .github/workflows/pages.yml    # GitHub Pages deployment workflow
```

## Local Development

To test the documentation site locally, you have two options:

### Option 1: With Gemfile (Recommended)
Create a `Gemfile` with GitHub Pages dependencies:
```ruby
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
```

Then:
```bash
bundle install
bundle exec jekyll serve
```

### Option 2: Direct Jekyll Installation
```bash
# Install Jekyll directly
gem install jekyll bundler

# Serve the site (may have version differences from GitHub Pages)
jekyll serve --baseurl /argorator
```

**View the site**: Open http://localhost:4000/argorator in your browser

## GitHub Pages Configuration

The site is automatically deployed via GitHub Actions when changes are pushed to the main branch.

### Key Configuration Files

- **`_config.yml`**: Jekyll configuration with site metadata, theme, and navigation
- **`Gemfile`**: (Optional) Ruby dependencies for local development
- **`.github/workflows/pages.yml`**: Automated deployment workflow

### Theme and Features

- **Theme**: Minima (default GitHub Pages theme)
- **Syntax Highlighting**: Rouge with line numbers
- **SEO**: Jekyll SEO plugin for better search engine optimization
- **Navigation**: Automatic header navigation from configured pages

## Adding New Documentation

1. **Create markdown files** in the appropriate directory under `docs/`
2. **Add Jekyll front matter** at the top:
   ```yaml
   ---
   layout: page
   title: Your Page Title
   permalink: /docs/your-page/
   ---
   ```
3. **Update navigation** in `_config.yml` if needed:
   ```yaml
   header_pages:
     - index.md
     - docs/README.md
     - docs/your-new-page.md
   ```

## URL Structure

- Main site: `https://dotle.github.io/argorator/`
- Documentation: `https://dotle.github.io/argorator/docs/`
- Features: `https://dotle.github.io/argorator/docs/features/`
- Changelog: `https://dotle.github.io/argorator/changelog/`

## Troubleshooting

### Local Build Issues

- **Ruby version conflicts**: Use rbenv or RVM to manage Ruby versions
- **Bundle install failures**: Make sure you have build tools installed
- **Port already in use**: Use `bundle exec jekyll serve --port 4001`

### GitHub Pages Issues

- **Build failures**: Check the Actions tab for detailed error logs
- **Pages not updating**: GitHub Pages can take a few minutes to deploy changes
- **404 errors**: Verify permalink paths match your navigation links