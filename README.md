# Vinay Prabhu · Personal website

Live site: https://vinayprabhu.github.io

A scholarly static website with 27 searchable research entries, projects, media, visual essays, and a complete text/link archive of the nine-page original Google Site.

## Build and edit

```bash
python -m pip install -r requirements.txt
python build.py
python -m http.server 8000 --directory dist
```

`build.py` automatically extracts `site-content.zip` into an ignored `content/` folder and generates the site in `dist/`. The browser needs no framework or external runtime libraries.

- Edit homepage, research presentation, and project copy in `build.py`.
- Edit typography/layout in `style.css` and interaction in `site.js`.
- Imported original text, links, images, and embed source are preserved in `site-content.zip`.
- Commit changes to `main`; the GitHub Actions workflow rebuilds and publishes the site automatically.
- To change imported content, edit `content/data/original-content.json`, then repack `content/assets`, `content/data`, and `content/archive` into `site-content.zip` with those relative paths intact.

## Migration record

Captured from https://www.vinayprabhu.com/ on 2026-11-08. All nine publicly linked same-domain pages were archived, including their original HTML, embedded-widget source, text, and links. 22 of 34 image URLs downloaded successfully; 12 returned HTTP 403 and remain recorded with their source URLs. Linked external websites, video streams, PDFs, and hosted interactive widgets are retained as links, not mirrored. The public archive page includes a downloadable copy of the original-site capture.

The homepage copy has been edited for clarity; collection pages preserve the original wording. No unverified publication venues or years were added. Thesis title/date were checked against https://kilthub.cmu.edu/articles/thesis/Network_Aided_Classification_and_Detection_of_Data/7430012. The portrait is the account's public GitHub avatar.

The original vinayprabhu.com domain and DNS remain unchanged. Legacy same-site routes are preserved; other GitHub project sites are unaffected.

## Validation

Desktop and 390px mobile layouts reviewed in Chrome. Search/category combinations, empty results, mobile menu, local links and asset paths checked. Semantic HTML, keyboard focus, reduced-motion support, print styles, and no analytics. Third-party players are opened through links rather than loaded automatically.

Original text, research images, and media retain their respective ownership; no blanket license for third-party material is implied.
