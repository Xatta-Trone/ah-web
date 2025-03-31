import requests
import json
import re
import os
import pandas as pd

# --- Helper Functions ---


def format_date(date_str):
    parts = date_str.split("/")
    if len(parts) == 1:
        return f"{parts[0]}-01-01"
    elif len(parts) == 2:
        return f"{parts[0]}-{parts[1].zfill(2)}-01"
    elif len(parts) == 3:
        return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
    else:
        return "Unknown"


def sanitize_text(text):
    if not text:
        return "Unknown"
    return re.sub(r"[\t\n\r]+", " ", text).strip()


def slugify(text):
    if not text:
        return "unknown"
    text = sanitize_text(text)
    text = re.sub(r'\s+', '-', text.lower())
    return re.sub(r'[^\w\-]', '', text)


# Escape YAML-sensitive characters
html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
}


def html_escape(text):
    return "".join(html_escape_table.get(c, c) for c in str(text))

# --- Load JSON Data from GitHub ---


url = "https://raw.githubusercontent.com/Xatta-Trone/google-scholar-scrapper/refs/heads/main/scholar-data-U9tD0ywAAAAJ.json"
response = requests.get(url)
json_data = response.json()

# Get total citations after loading JSON data
total_citations = 0

# --- Extract and Transform ---

records = []
for pub in json_data["data"]:
    title = sanitize_text(pub.get("title", ""))
    venue = sanitize_text(pub.get("journal") or pub.get(
        "conference") or pub.get("book") or pub.get("institution") or "Unknown")
    authors = pub.get("authors", "")
    year = pub.get("year", "Unknown")
    # Convert citation count to int, default to 0 if empty string or invalid
    pub_citations = pub.get("total_citations", "0")
    if not pub_citations or not str(pub_citations).strip():
        pub_citations = 0
    else:
        try:
            pub_citations = int(pub_citations)
        except (ValueError, TypeError):
            pub_citations = 0

    total_citations += pub_citations

    records.append({
        "pub_date": format_date(pub.get("publication_date", "Unknown")),
        "title": title,
        "venue": venue,
        "excerpt": sanitize_text(pub.get("description", "")[:200] + "...") if pub.get("description") else "",
        "citation": sanitize_text(f'{authors} ({year}). "{title}" {venue}.'),
        "url_slug": slugify(title),
        "paper_url": sanitize_text(pub.get("source_url") or pub.get("url") or "")
    })

# --- Convert to DataFrame ---
df = pd.DataFrame(records)

# --- Generate Markdown Files ---

output_folder = "../_publications/"
os.makedirs(output_folder, exist_ok=True)

new_files_count = 0  # Counter for new files

for _, item in df.iterrows():
    url_slug = item.get("url_slug", "").strip()
    pub_date = str(item.get("pub_date", "Unknown")).strip()
    if pub_date == "Unknown" or not url_slug:
        continue

    md_filename = f"{pub_date}-{url_slug}.md"
    html_filename = f"{pub_date}-{url_slug}"
    output_path = os.path.join(output_folder, md_filename)

    if os.path.exists(output_path):
        continue  # Skip existing file

    title = html_escape(item.get("title", "Untitled"))
    venue = html_escape(item.get("venue", "N/A"))
    excerpt = html_escape(item.get("excerpt", ""))
    citation = html_escape(item.get("citation", ""))
    paper_url = item.get("paper_url", "").strip()

    md = f"""---
title: "{title}"
collection: publications
permalink: /publication/{html_filename}
date: {pub_date}
venue: '{venue}'
category: manuscripts
"""

    if excerpt:
        md += f"excerpt: '{excerpt}'\n"
    if paper_url:
        md += f"paperurl: '{paper_url}'\n"
    md += f"citation: '{citation}'\n---\n"

    if paper_url:
        md += f"\n<a href='{paper_url}'>Download paper here</a>\n"
    if excerpt and excerpt != "Unknown":
        md += f"\n{excerpt}\n"

    md += f"\nRecommended citation: {citation}"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    new_files_count += 1  # Increment new file counter

# Update citation count in specified files


def update_citation_count(file_path, citation_count):
    if not os.path.exists(file_path):
        print(f"⚠️ File not found: {file_path}")
        return False

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Update citation count with current date
    current_date = pd.Timestamp.now().strftime('%d %B %Y')
    new_citation_line = f"**Google Scholar citations:** {citation_count} *(as of {current_date})*"

    # Replace existing citation line without affecting the next line
    updated_content = re.sub(
        r'\*\*Google Scholar citations:\*\*.*?\(as of .*?\)\*',
        new_citation_line,
        content
    )

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    return True



# After generating publications, update citation counts
files_to_update = [
    "../_pages/about.md",
    "../_pages/highlights.md"
]

for file_path in files_to_update:
    if update_citation_count(file_path, total_citations):
        print(f"✅ Updated citations in {os.path.basename(file_path)}")

print(
    f"✅ All updates complete! ({new_files_count} new publications, {total_citations} total citations)")
