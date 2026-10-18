# Portfolio Readme

## How to develop

Contents are stored in `site.yaml`

```yaml
- slug: "slug-how-it-appears-in-the-url"
  title: "Project Title, cover title can be different from the title in the post itself"
  description: >-
    A short description of the project, supporting markdown, must be 420-575 characters.
  category: "either Homelab, Development or Media"
  type: "🏆 1st Place Hackathon Winner"
  tags: ["Python", "Flask", "React", "Leaflet", "Machine Learning", "Hackathon"]
  url: "https://www.bcit.ca/news/stories/computing-takes-first-place/"
  images:
    - url: "/static/images/image-name.webp"
      alt: "image alt"
    - url: "/static/images/image-name2.webp"
      alt: "image alt 2"
  start_date: unquoted date in format YYYY-MM-DD
  end_date: unquoted date in format YYYY-MM-DD
  featured: true
  read_more: "alternate text to display on the url"
```

Refer to the [feature-image-safe-area.svg](feature-image-safe-area.svg) when designing cover images, the aspect ratio for mobile and desktop is different

## Writing posts

Post are authored in markdown and stored in the `content` folder, support common markdown features.

Linking uses `[label](post-name-without-extension)`

Images must be placed in the `static/images` folder and referenced with `/static/images/image-name.webp`

- this site currently do not support publishing via subfolders, only `/` is supported.

Individual posts require the frontmatter

```yaml
---
title: "Project Title"
date: unquoted date in format YYYY-MM-DD
---
```

### Limitations

- headers must be available or table of content won't render properly
- back to back admonition is not supported, must be separated
- must contain at least one or more second level header (##)
- only note admonition is supported, other types won't work

## Add or preview the site

### Start the dev server

```bash
uv run dev.py
```

### Build the site

```bash
uv run build.py
```

### Check before publishing

```bash
uv run lint.py
```

## Update resume

```bash
uv run compress_resume.py new_resume.pdf /static/resume.pdf
```
