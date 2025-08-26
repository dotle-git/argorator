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

To test the documentation site locally:

1. **Install Ruby and Bundler** (if not already installed):
   ```bash
   # On macOS with Homebrew
   brew install ruby
   
   # On Ubuntu/Debian
   sudo apt-get install ruby-full build-essential zlib1g-dev
   
   # Install Bundler
   gem install bundler
   ```

2. **Install dependencies**:
   ```bash
   bundle install
   ```

3. **Run the local server**:
   ```bash
   bundle exec jekyll serve
   ```

4. **View the site**:
   Open http://localhost:4000/argorator in your browser

## GitHub Pages Configuration

The site is automatically deployed via GitHub Actions when changes are pushed to the main branch.

### Key Configuration Files

- **`_config.yml`**: Jekyll configuration with site metadata, theme, and navigation
- **`Gemfile`**: Ruby dependencies compatible with GitHub Pages
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