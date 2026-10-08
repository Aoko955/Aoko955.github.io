#!/usr/bin/env python3
"""Build preview.html or static _site/ for GitHub Pages (no Jekyll)."""
from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def parse_site_title(config_text: str) -> str:
    m = re.search(r'^title\s*:\s*"(.*)"\s*$', config_text, re.M)
    return m.group(1) if m else "Homepage"


def parse_author(config_text: str) -> dict[str, str]:
    author: dict[str, str] = {}
    in_author = False
    for line in config_text.splitlines():
        if line.strip() == "author:":
            in_author = True
            continue
        if in_author:
            if re.match(r"^[a-z]", line) and not line.startswith(" "):
                break
            m = re.match(r"^\s+(\w+)\s*:\s*(.*)$", line)
            if m:
                val = m.group(2).strip().strip('"')
                author[m.group(1)] = val
    return author


def strip_front_matter(md: str) -> str:
    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end != -1:
            return md[end + 4 :].lstrip("\n")
    return md


def apply_liquid(content: str, author: dict[str, str]) -> str:
    content = content.replace("{{ site.author.googlescholar }}", author.get("googlescholar", "#"))
    content = re.sub(r"\{\{\s*site\.time\s*\|\s*date:\s*['\"]%s['\"]\s*\}\}", "", content)
    content = re.sub(r"\{\{\s*site\.time\s*\|\s*date:\s*[\"']%s[\"']\s*\}\}", "", content)
    content = re.sub(r"\?v=\s*\"", '"', content)
    content = re.sub(r"\?v=\s*'", "'", content)
    return content


def md_light(text: str) -> str:
    lines = []
    in_news = False
    for line in text.splitlines():
        if 'class="news-box"' in line:
            in_news = True
            lines.append(line)
            continue
        if in_news and line.strip() == "</div>":
            in_news = False
            lines.append(line)
            continue
        if in_news and line.startswith("- "):
            body = line[2:].strip()
            body = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", body)
            body = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", body)
            lines.append(f"<li>{body}</li>")
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            title = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', title)
            lines.append(f"<h1>{title}</h1>")
            continue
        s = line
        if not s.lstrip().startswith("<"):
            s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
            s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        lines.append(s)
    out = "\n".join(lines)
    out = re.sub(
        r'(<div class="news-box"[^>]*>)\n((?:<li>.*\n)+)',
        r"\1<ul>\n\2</ul>\n",
        out,
    )
    return out


def hero_html(author: dict[str, str]) -> str:
    name = author.get("name", "Name")
    name_cn = author.get("name_cn", "")
    cn = f' <span class="hero__name-cn">{name_cn}</span>' if name_cn else ""
    bio = author.get("bio", "")
    loc = author.get("location", "")
    email = author.get("email", "")
    gs = author.get("googlescholar", "")
    gh = author.get("github", "")
    cv = author.get("cv", "")
    avatar = author.get("avatar", "")

    links = []
    if email:
        links.append(
            f'<a href="mailto:{email}"><i class="fas fa-envelope"></i> Email</a>'
        )
    if gs:
        links.append(
            f'<a href="{gs}" target="_blank" rel="noopener"><i class="ai ai-google-scholar"></i> Scholar</a>'
        )
    if gh:
        links.append(
            f'<a href="https://github.com/{gh}" target="_blank" rel="noopener"><i class="fab fa-github"></i> GitHub</a>'
        )
    if cv:
        links.append(
            f'<a href="/{cv}" target="_blank" rel="noopener"><i class="fas fa-file-lines"></i> CV</a>'
        )
    links_html = "\n            ".join(links)

    photo = ""
    if avatar:
        photo = f"""
        <div class="hero__photo">
          <img src="/{avatar}" alt="{name}">
        </div>"""

    loc_html = ""
    if loc:
        loc_html = f'<p class="hero__loc"><i class="fas fa-location-dot"></i> {loc}</p>'

    return f"""
      <section class="hero">
        <div class="hero__text">
          <h1 class="hero__name">{name}{cn}</h1>
          <p class="hero__role">{bio}</p>
          {loc_html}
          <div class="hero__links">
            {links_html}
          </div>
        </div>{photo}
      </section>"""


def render_html(config_text: str, body: str, *, for_publish: bool) -> str:
    author = parse_author(config_text)
    site_title = parse_site_title(config_text)
    year = datetime.now(timezone.utc).strftime("%Y")
    month_year = datetime.now(timezone.utc).strftime("%b %Y")

    if for_publish:
        footer = (
            f'<p>&copy; {year} {author.get("name", "")}. '
            f'Last updated {month_year}.</p>'
        )
        page_title = site_title
    else:
        footer = "<p>Local preview — run <code>python3 build_preview.py</code> after edits.</p>"
        page_title = f"{author.get('name', 'Homepage')} | preview"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <script>
    (function () {{
      try {{
        var t = localStorage.getItem('theme') ||
          (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        document.documentElement.setAttribute('data-theme', t);
      }} catch (e) {{}}
    }})();
  </script>
  <link rel="stylesheet" href="/stylesheet.css">
  <link rel="stylesheet" href="/jon-extra.css">
  <link rel="stylesheet" href="/assets/css/academicons.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
</head>
<body>
  <header class="site-nav" id="site-nav">
    <div class="site-nav__inner">
      <a class="site-nav__brand" href="#top">{author.get("name", "")}</a>
      <div class="site-nav__right">
        <nav class="site-nav__links" aria-label="Primary">
          <a href="#about-me">About</a>
          <a href="#-news">News</a>
          <a href="#-publications">Publications</a>
          <a href="#-educations">Education</a>
          <a href="#-experience">Experience</a>
        </nav>
        <button class="theme-toggle" id="theme-toggle" type="button" aria-label="Toggle dark mode">
          <i class="fas fa-moon"></i><i class="fas fa-sun"></i>
        </button>
      </div>
    </div>
  </header>
  <main class="wrap" id="top">
{hero_html(author)}
    <div class="content">
{body}
    </div>
    <footer class="site-footer">
      {footer}
    </footer>
  </main>
  <a href="#top" class="to-top" aria-label="Back to top"><i class="fas fa-arrow-up"></i></a>
  <script>
    (function () {{
      var nav = document.getElementById('site-nav');
      var sections = ['about-me', '-news', '-publications', '-educations', '-experience']
        .map(function (id) {{ return document.getElementById(id); }})
        .filter(Boolean);
      var navLinks = Array.prototype.slice.call(document.querySelectorAll('.site-nav__links a'));

      function onScroll() {{
        if (window.scrollY > 24) {{ nav.classList.add('is-scrolled'); }}
        else {{ nav.classList.remove('is-scrolled'); }}
        var current = '';
        var probe = window.scrollY + 120;
        sections.forEach(function (sec) {{
          if (sec.offsetTop <= probe) {{ current = sec.id; }}
        }});
        navLinks.forEach(function (link) {{
          var active = link.getAttribute('href') === '#' + current;
          link.classList.toggle('is-active', active);
        }});
        var toTop = document.querySelector('.to-top');
        if (toTop) {{ toTop.classList.toggle('is-visible', window.scrollY > 600); }}
      }}
      window.addEventListener('scroll', onScroll, {{ passive: true }});
      onScroll();


      document.getElementById('theme-toggle')?.addEventListener('click', function () {{
        var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        try {{ localStorage.setItem('theme', next); }} catch (e) {{}}
      }});
    }})();
  </script>
</body>
</html>
"""


def publish_static(html: str) -> None:
    site = ROOT / "_site"
    if site.exists():
        shutil.rmtree(site)
    site.mkdir()

    (site / "index.html").write_text(html, encoding="utf-8")
    shutil.copy2(ROOT / "stylesheet.css", site / "stylesheet.css")
    shutil.copy2(ROOT / "jon-extra.css", site / "jon-extra.css")
    shutil.copytree(ROOT / "images", site / "images")

    css_dir = site / "assets" / "css"
    fonts_dir = site / "assets" / "fonts"
    css_dir.mkdir(parents=True)
    fonts_dir.mkdir(parents=True)
    shutil.copy2(ROOT / "assets/css/academicons.css", css_dir / "academicons.css")
    for font in (ROOT / "assets/fonts").glob("academicons.*"):
        shutil.copy2(font, fonts_dir / font.name)

    print(f"Wrote {site}/index.html and static assets")


def build_body() -> str:
    config = (ROOT / "_config.yml").read_text(encoding="utf-8")
    author = parse_author(config)
    body = strip_front_matter((ROOT / "_pages" / "about.md").read_text(encoding="utf-8"))
    body = apply_liquid(body, author)
    return md_light(body), config


def build(*, site: bool = False) -> None:
    body, config = build_body()
    html = render_html(config, body, for_publish=site)

    if site:
        publish_static(html)
        return

    preview_paths = (ROOT / "preview.html",)
    for path in preview_paths:
        # Local preview uses relative asset URLs
        local_html = html.replace('href="/stylesheet.css"', 'href="stylesheet.css"')
        local_html = local_html.replace('href="/jon-extra.css"', 'href="jon-extra.css"')
        local_html = local_html.replace('href="/assets/', 'href="assets/')
        local_html = local_html.replace('src="/images/', 'src="images/')
        local_html = local_html.replace('href="/images/', 'href="images/')
        path.write_text(local_html, encoding="utf-8")
        print(f"Wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--site",
        action="store_true",
        help="Build _site/ for GitHub Pages (same content as preview)",
    )
    args = parser.parse_args()
    build(site=args.site)


if __name__ == "__main__":
    main()
