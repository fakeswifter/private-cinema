#!/usr/bin/env python3
"""
Build static HTML site from movie + live music review markdown files.
Pitchfork-inspired editorial design.
"""
import re
import os
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
LIVE_ROOT = Path("/Users/jinghaoyan/live-music-reviews")
OUT_DIR = ROOT / "docs"


# ── Parsers ──────────────────────────────────────────────────────────

def parse_movie_md(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:])

    data = {
        "type": "film",
        "title": title,
        "filename": path.stem,
        "body_md": body.strip(),
        "date": None,
        "director": "待补充",
        "cast": [],
        "year": "",
        "runtime": "",
        "my_rating": "待定",
        "summary": "",
    }

    for line in lines:
        if line.startswith("- **观影日期**"):
            data["date"] = _extract_val(line)
        elif line.startswith("- **导演**"):
            data["director"] = _extract_val(line)
        elif line.startswith("- **主演**"):
            cast_str = _extract_val(line)
            data["cast"] = [c.strip() for c in cast_str.split("/")]
        elif line.startswith("- **年份**"):
            data["year"] = _extract_val(line)
        elif line.startswith("- **片长**"):
            data["runtime"] = _extract_val(line)
        elif line.startswith("- **我的评分**"):
            data["my_rating"] = _extract_val(line)

    sm = re.search(r'\*\*一句话总结\*\*[：:]\s*(.+?)(?:\n|$)', body)
    if sm:
        data["summary"] = sm.group(1)

    # Normalize rating to a clean number or tuple
    data["rating_num"] = _parse_rating(data["my_rating"])
    return data


def parse_live_md(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.strip().split("\n")
    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:])

    data = {
        "type": "live",
        "title": title,
        "filename": path.stem,
        "body_md": body.strip(),
        "date": None,
        "artist": "",
        "venue": "",
        "style": "",
        "my_rating": "待定",
        "summary": "",
    }

    for line in lines:
        if line.startswith("- **演出日期**"):
            data["date"] = _extract_val(line)
        elif line.startswith("- **艺人**"):
            data["artist"] = _extract_val(line)
        elif line.startswith("- **场地**"):
            data["venue"] = _extract_val(line)
        elif line.startswith("- **风格**"):
            data["style"] = _extract_val(line)
        elif line.startswith("- **我的评分**"):
            data["my_rating"] = _extract_val(line)

    sm = re.search(r'\*\*一句话总结\*\*[：:]\s*(.+?)(?:\n|$)', body)
    if sm:
        data["summary"] = sm.group(1)

    data["rating_num"] = _parse_rating(data["my_rating"])
    return data


def _extract_val(line: str) -> str:
    if "：" in line:
        return line.split("：")[-1].strip()
    return line.split(":**")[-1].strip() if ":**" in line else line.strip()


def _parse_rating(raw: str):
    raw = raw.strip()
    m = re.search(r'(\d+(?:\.\d+)?)', raw)
    if m:
        return float(m.group(1))
    return None


# ── Markdown → HTML ──────────────────────────────────────────────────

def md_to_html(md_text: str) -> str:
    html = md_text
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*</li>)', r'<ul>\n\1\n</ul>', html, flags=re.DOTALL)
    html = html.replace('</ul>\n<ul>', '\n')
    paragraphs = html.split('\n\n')
    result = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith('<h') or p.startswith('<ul') or p.startswith('<li'):
            result.append(p)
        else:
            result.append(f'<p>{p}</p>')
    return '\n'.join(result)


# ── CSS ──────────────────────────────────────────────────────────────

CSS = """\
    :root {
      --bg: #0d0d0d;
      --surface: #141414;
      --text: #d4d4d4;
      --text-dim: #888888;
      --text-bright: #f0f0f0;
      --accent: #e8a838;
      --accent-film: #d4756b;
      --accent-live: #6bb5d4;
      --border: #2a2a2a;
      --border-light: #1f1f1f;
      --score-bg: #1a1a1a;
      --hero-bg: #151515;
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
                   "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }

    /* ── Masthead ─────────────────────────────── */
    .masthead {
      border-bottom: 1px solid var(--border);
      padding: 40px 0 18px;
      text-align: center;
      margin-bottom: 0;
    }
    .masthead .logo {
      font-family: "Georgia", "Times New Roman", "Noto Serif SC", "SimSun", serif;
      font-size: 2.8rem;
      font-weight: 700;
      letter-spacing: 0.02em;
      color: var(--text-bright);
      text-decoration: none;
      display: inline-block;
    }
    .masthead .logo:hover { color: var(--accent); }
    .masthead .tagline {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.35em;
      color: var(--text-dim);
      margin-top: 6px;
    }

    /* ── Nav ──────────────────────────────────── */
    .nav {
      display: flex;
      justify-content: center;
      gap: 40px;
      padding: 16px 0;
      border-bottom: 1px solid var(--border-light);
      margin-bottom: 2px;
    }
    .nav a {
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.25em;
      color: var(--text-dim);
      text-decoration: none;
      font-weight: 500;
      padding-bottom: 4px;
      border-bottom: 2px solid transparent;
      transition: all 0.15s;
    }
    .nav a:hover,
    .nav a.active {
      color: var(--text-bright);
      border-bottom-color: var(--accent);
    }

    /* ── Layout ───────────────────────────────── */
    .container { max-width: 1020px; margin: 0 auto; padding: 0 24px; }
    .content { padding: 32px 0 60px; }

    /* ── Hero (featured) ──────────────────────── */
    .hero {
      display: grid;
      grid-template-columns: 1fr 120px;
      gap: 40px;
      align-items: start;
      padding: 40px 0 36px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 40px;
    }
    .hero .hero-tag {
      font-size: 0.68rem;
      text-transform: uppercase;
      letter-spacing: 0.3em;
      font-weight: 600;
      color: var(--accent);
      margin-bottom: 10px;
    }
    .hero .hero-title {
      font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif;
      font-size: 2.4rem;
      font-weight: 700;
      line-height: 1.25;
      color: var(--text-bright);
      margin-bottom: 14px;
    }
    .hero .hero-title a {
      color: var(--text-bright);
      text-decoration: none;
    }
    .hero .hero-title a:hover { color: var(--accent); }
    .hero .hero-meta {
      font-size: 0.82rem;
      color: var(--text-dim);
      margin-bottom: 14px;
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
      align-items: center;
    }
    .hero .hero-meta .sep { color: #444; }
    .hero .hero-summary {
      font-size: 1.05rem;
      line-height: 1.6;
      color: #aaa;
      font-style: italic;
      margin-bottom: 16px;
    }
    .hero .hero-link {
      display: inline-block;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.2em;
      color: var(--accent);
      text-decoration: none;
      font-weight: 600;
      border-bottom: 1px solid var(--accent);
      padding-bottom: 2px;
      transition: opacity 0.15s;
    }
    .hero .hero-link:hover { opacity: 0.7; }

    /* ── Score badge ──────────────────────────── */
    .score-badge {
      width: 96px;
      height: 96px;
      border-radius: 50%;
      background: var(--score-bg);
      border: 3px solid var(--border);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0px;
      flex-shrink: 0;
    }
    .score-badge .score-num {
      font-family: "Georgia", "Times New Roman", serif;
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--text-bright);
      line-height: 1;
    }
    .score-badge .score-label {
      font-size: 0.55rem;
      text-transform: uppercase;
      letter-spacing: 0.2em;
      color: var(--text-dim);
      margin-top: 2px;
    }
    .score-badge.film { border-color: var(--accent-film); }
    .score-badge.film .score-num { color: var(--accent-film); }
    .score-badge.live { border-color: var(--accent-live); }
    .score-badge.live .score-num { color: var(--accent-live); }

    @media (max-width: 640px) {
      .hero { grid-template-columns: 1fr; }
      .hero .score-wrap { order: -1; }
      .hero .hero-title { font-size: 1.6rem; }
      .score-badge { width: 64px; height: 64px; }
      .score-badge .score-num { font-size: 1.5rem; }
    }

    /* ── Section headers ──────────────────────── */
    .section-head {
      font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif;
      font-size: 1.3rem;
      font-weight: 700;
      color: var(--text-bright);
      margin: 44px 0 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid var(--border);
    }
    .section-head .count {
      font-size: 0.75rem;
      color: var(--text-dim);
      font-weight: 400;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin-left: 12px;
    }

    /* ── Review grid ──────────────────────────── */
    .review-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 28px;
    }
    .review-card {
      background: var(--surface);
      border: 1px solid var(--border);
      padding: 24px 28px;
      display: flex;
      flex-direction: column;
      transition: border-color 0.2s;
    }
    .review-card:hover { border-color: #404040; }
    .review-card .card-tag {
      font-size: 0.6rem;
      text-transform: uppercase;
      letter-spacing: 0.35em;
      font-weight: 700;
      margin-bottom: 14px;
    }
    .card-tag.film { color: var(--accent-film); }
    .card-tag.live { color: var(--accent-live); }
    .review-card .card-title {
      font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif;
      font-size: 1.15rem;
      font-weight: 700;
      line-height: 1.35;
      color: var(--text-bright);
      margin-bottom: 8px;
    }
    .review-card .card-title a {
      color: var(--text-bright);
      text-decoration: none;
    }
    .review-card .card-title a:hover { color: var(--accent); }
    .review-card .card-meta {
      font-size: 0.72rem;
      color: var(--text-dim);
      margin-bottom: 12px;
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .review-card .card-summary {
      font-size: 0.85rem;
      color: #999;
      line-height: 1.5;
      flex: 1;
    }
    .review-card .card-bottom {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      margin-top: 16px;
      gap: 12px;
    }
    .review-card .card-score {
      font-family: "Georgia", "Times New Roman", serif;
      font-size: 2rem;
      font-weight: 700;
      line-height: 1;
      flex-shrink: 0;
    }
    .card-score.film { color: var(--accent-film); }
    .card-score.live { color: var(--accent-live); }
    .review-card .card-read {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.2em;
      color: var(--text-dim);
      text-decoration: none;
      font-weight: 600;
      white-space: nowrap;
    }
    .review-card .card-read:hover { color: var(--accent); }

    /* ── Empty state ──────────────────────────── */
    .empty-state {
      text-align: center;
      padding: 60px 0;
      color: var(--text-dim);
    }
    .empty-state .icon { font-size: 2.5rem; margin-bottom: 12px; }

    /* ── Detail page ──────────────────────────── */
    .back-link {
      display: inline-block;
      color: var(--text-dim);
      text-decoration: none;
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.2em;
      margin-bottom: 28px;
    }
    .back-link:hover { color: var(--text-bright); }
    .detail-header {
      margin-bottom: 36px;
      padding-bottom: 28px;
      border-bottom: 1px solid var(--border);
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 32px;
      align-items: start;
    }
    .detail-header h1 {
      font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif;
      font-size: 2.2rem;
      font-weight: 700;
      color: var(--text-bright);
      line-height: 1.25;
      margin-bottom: 14px;
    }
    .detail-meta-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 10px 20px;
    }
    .detail-meta-item {
      font-size: 0.8rem;
      color: var(--text-dim);
    }
    .detail-meta-item strong { color: #999; font-weight: 400; display: block; font-size: 0.68rem; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 2px; }
    .detail-body {
      color: #bbb;
      font-size: 0.95rem;
    }
    .detail-body h2 {
      font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif;
      font-size: 1.25rem;
      font-weight: 600;
      color: #ddd;
      margin: 32px 0 12px;
    }
    .detail-body h3 {
      font-size: 1rem;
      font-weight: 500;
      color: #ccc;
      margin: 22px 0 8px;
    }
    .detail-body p { margin-bottom: 14px; }
    .detail-body ul { margin: 8px 0 16px 22px; }
    .detail-body li { margin-bottom: 5px; }
    .detail-body strong { color: #ddd; font-weight: 500; }

    @media (max-width: 600px) {
      .detail-header { grid-template-columns: 1fr; }
      .detail-header h1 { font-size: 1.5rem; }
    }

    /* ── Footer ───────────────────────────────── */
    footer {
      text-align: center;
      color: #3a3a3a;
      font-size: 0.72rem;
      margin-top: 60px;
      padding: 28px 0;
      border-top: 1px solid var(--border);
    }
    footer span { margin: 0 20px; }

    /* ── AI Comment Section ───────────────────── */
    .comment-section {
      margin-top: 48px;
      padding-top: 36px;
      border-top: 2px solid var(--border);
    }
    .comment-section-title {
      font-family: "Georgia", "Times New Roman", "Noto Serif SC", serif;
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-bright);
      margin-bottom: 24px;
      letter-spacing: 0.02em;
    }
    .comment-section-title .subtitle {
      font-size: 0.65rem;
      text-transform: uppercase;
      letter-spacing: 0.3em;
      color: var(--text-dim);
      font-weight: 400;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin-left: 12px;
    }
    .comment-card {
      background: var(--surface);
      border: 1px solid var(--border);
      padding: 22px 26px;
      margin-bottom: 16px;
    }
    .comment-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .comment-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: var(--score-bg);
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1rem;
      flex-shrink: 0;
    }
    .comment-name {
      font-size: 0.9rem;
      font-weight: 600;
      color: #ddd;
    }
    .comment-role {
      font-size: 0.68rem;
      color: var(--text-dim);
      font-weight: 400;
    }
    .comment-body {
      font-size: 0.88rem;
      color: #aaa;
      line-height: 1.75;
    }
"""


# ── Generators ───────────────────────────────────────────────────────

def score_badge_html(rating_num, rtype, size="lg"):
    """Pitchfork-style circular score badge."""
    if rating_num is None:
        return ""
    cls = f"score-badge {rtype}"
    num = str(rating_num).rstrip('0').rstrip('.') if '.' in str(rating_num) else str(int(rating_num))
    label = "SCORE"
    return f"""\
                <div class="{cls}">
                  <div class="score-num">{num}</div>
                  <div class="score-label">{label}</div>
                </div>"""


def format_date(d):
    """Nicely format YYYY-MM-DD for display."""
    if not d:
        return ""
    try:
        dt = datetime.strptime(d.strip(), "%Y-%m-%d")
        return dt.strftime("%B %d, %Y")
    except:
        return d


def generate_index(reviews):
    if not reviews:
        return _html_shell(
            "PRIVATE CINEMA · 私人影院",
            '<div class="content"><div class="empty-state"><div class="icon">🎬</div><p>还没有记录</p></div></div>'
        )

    # Hero: most recent review
    hero = reviews[0]
    hero_html = _hero_block(hero)
    if hero is None:
        hero_html = ""

    # Group by type
    films = [r for r in reviews if r["type"] == "film"]
    lives = [r for r in reviews if r["type"] == "live"]

    content = '<div class="content">'
    content += hero_html

    if films:
        film_s = "s" if len(films) > 1 else ""
        content += f'<div class="section-head" id="film">Film 电影<span class="count">{len(films)} review{film_s}</span></div>'
        content += '<div class="review-grid">'
        for r in films:
            content += _card_html(r)
        content += '</div>'

    if lives:
        live_s = "s" if len(lives) > 1 else ""
        content += f'<div class="section-head" id="live">Live 现场<span class="count">{len(lives)} review{live_s}</span></div>'
        content += '<div class="review-grid">'
        for r in lives:
            content += _card_html(r)
        content += '</div>'

    content += '</div>'
    return _html_shell("PRIVATE CINEMA · 私人影院", content)


def _hero_block(r):
    if r is None:
        return ""
    rtype = r["type"]
    tag = "Film" if rtype == "film" else "Live"
    badge = score_badge_html(r["rating_num"], rtype)
    summary_html = f'<div class="hero-summary">{r["summary"]}</div>' if r["summary"] else ""
    date_str = format_date(r["date"])
    meta_parts = []
    if date_str:
        meta_parts.append(date_str)
    if rtype == "film":
        if r.get("director") and r["director"] != "待补充":
            meta_parts.append(r["director"])
        if r.get("year"):
            meta_parts.append(r["year"])
    else:
        if r.get("venue"):
            meta_parts.append(r.get("venue", "").split("，")[0].split(",")[0])
        if r.get("style"):
            meta_parts.append(r["style"])

    meta = ' · '.join(meta_parts)

    return f"""\
            <div class="hero">
              <div>
                <div class="hero-tag">{tag} / LATEST</div>
                <div class="hero-title"><a href="{r['filename']}.html">{r['title']}</a></div>
                <div class="hero-meta">{meta}</div>
                {summary_html}
                <a href="{r['filename']}.html" class="hero-link">Read Review →</a>
              </div>
              <div class="score-wrap">{badge}</div>
            </div>"""


def _card_html(r):
    rtype = r["type"]
    tag = "Film" if rtype == "film" else "Live"
    tag_cls = "film" if rtype == "film" else "live"
    summary_html = f'<div class="card-summary">{r["summary"]}</div>' if r["summary"] else ""
    date_str = format_date(r["date"])
    meta_parts = []
    if date_str:
        meta_parts.append(date_str)
    if rtype == "film" and r.get("director") and r["director"] != "待补充":
        meta_parts.append(r["director"])
    elif rtype == "live" and r.get("artist"):
        meta_parts.append(r["artist"])

    meta = ' · '.join(meta_parts)
    rating_num = r["rating_num"]
    score_html = ""
    if rating_num is not None:
        num_str = str(rating_num).rstrip('0').rstrip('.') if '.' in str(rating_num) else str(int(rating_num))
        score_html = f'<div class="card-score {tag_cls}">{num_str}</div>'

    return f"""\
            <article class="review-card">
              <div class="card-tag {tag_cls}">{tag}</div>
              <div class="card-title"><a href="{r['filename']}.html">{r['title']}</a></div>
              <div class="card-meta">{meta}</div>
              {summary_html}
              <div class="card-bottom">
                <a href="{r['filename']}.html" class="card-read">Read →</a>
                {score_html}
              </div>
            </article>"""


def generate_review_page(r, comments=None):
    body_html = md_to_html(r["body_md"])
    rtype = r["type"]
    tag = "Film" if rtype == "film" else "Live"

    # Build meta grid
    meta_items = []
    if rtype == "film":
        meta_items.append(("DATE", r["date"] or "—"))
        meta_items.append(("DIRECTOR", r.get("director", "—")))
        cast_str = ", ".join(r.get("cast", []))
        meta_items.append(("CAST", cast_str if cast_str else "—"))
        meta_items.append(("YEAR", r.get("year", "—")))
        meta_items.append(("RUNTIME", r.get("runtime", "—")))
        meta_items.append(("RATING", r.get("my_rating", "—")))
    else:
        meta_items.append(("DATE", r["date"] or "—"))
        meta_items.append(("ARTIST", r.get("artist", "—")))
        meta_items.append(("VENUE", r.get("venue", "—")))
        meta_items.append(("STYLE", r.get("style", "—")))
        meta_items.append(("RATING", r.get("my_rating", "—")))

    meta_grid = "\n".join(
        f'<div class="detail-meta-item"><strong>{label}</strong> {val}</div>'
        for label, val in meta_items
    )

    badge = score_badge_html(r["rating_num"], rtype) if r["rating_num"] is not None else ""

    # Generate comment section if comments available
    comment_html = ""
    if comments and r["filename"] in comments:
        comment_html = _comment_section_html(comments[r["filename"]])

    content = f"""\
            <a href="index.html" class="back-link">← Home</a>
            <div class="detail-header">
              <div>
                <div style="font-size:0.68rem;text-transform:uppercase;letter-spacing:0.3em;color:var(--accent);margin-bottom:8px;">{tag}</div>
                <h1>{r['title']}</h1>
                <div class="detail-meta-grid">
                  {meta_grid}
                </div>
              </div>
              {badge}
            </div>
            <div class="detail-body">
              {body_html}
            </div>
            {comment_html}"""

    full_content = f'<div class="content">{content}</div>'
    return _html_shell(f"{r['title']} · Private Cinema", full_content)


def _comment_section_html(comment_list):
    """Generate HTML for the AI comment section."""
    cards = ""
    for c in comment_list:
        comment_text = c["comment"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        cards += f"""\
            <div class="comment-card">
              <div class="comment-header">
                <div class="comment-avatar">{c['avatar']}</div>
                <div>
                  <div class="comment-name">{c['name']}</div>
                  <div class="comment-role">{c['role']}</div>
                </div>
              </div>
              <div class="comment-body">{comment_text}</div>
            </div>"""

    return f"""\
            <div class="comment-section">
              <div class="comment-section-title">
                AI 评论团<span class="subtitle">· DEEPSEEK</span>
              </div>
              {cards}
            </div>"""


def _html_shell(title, content):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{CSS}</style>
</head>
<body>
  <header class="masthead">
    <a href="index.html" class="logo">PRIVATE CINEMA</a>
    <div class="tagline">Movies & Live · A Personal Journal</div>
  </header>
  <nav class="nav">
    <a href="index.html" class="active">Home</a>
    <a href="index.html#film">Film</a>
    <a href="index.html#live">Live</a>
  </nav>
  <div class="container">
    {content}
    <footer>
      <span>A personal archive of film and live music experiences.</span>
    </footer>
  </div>
</body>
</html>"""


# ── Build ────────────────────────────────────────────────────────────

def build():
    OUT_DIR.mkdir(exist_ok=True)

    reviews = []

    # Collect movie reviews
    for f in sorted(ROOT.glob("*.md"), reverse=True):
        if f.name == "README.md":
            continue
        data = parse_movie_md(f)
        reviews.append(data)

    # Collect live music reviews
    if LIVE_ROOT.exists():
        for f in sorted(LIVE_ROOT.glob("*.md"), reverse=True):
            data = parse_live_md(f)
            reviews.append(data)

    # Sort all by date descending
    def sort_key(r):
        d = r.get("date") or "0000-00-00"
        return d
    reviews.sort(key=sort_key, reverse=True)

    # Load AI comments if available
    comments = {}
    comments_path = OUT_DIR / "comments.json"
    if comments_path.exists():
        comments = json.loads(comments_path.read_text(encoding="utf-8"))
        print(f"  Loaded comments for {len(comments)} review(s)")

    # Generate index
    index_html = generate_index(reviews)
    (OUT_DIR / "index.html").write_text(index_html, encoding="utf-8")

    # Generate individual pages
    for r in reviews:
        review_html = generate_review_page(r, comments)
        (OUT_DIR / f"{r['filename']}.html").write_text(review_html, encoding="utf-8")

    film_count = sum(1 for r in reviews if r["type"] == "film")
    live_count = sum(1 for r in reviews if r["type"] == "live")
    print(f"✓ Built → {OUT_DIR}")
    print(f"  {film_count} film review(s) + {live_count} live review(s)")


if __name__ == "__main__":
    build()
