import pandas as pd
import os

# Load the TSV file correctly
file_path = "https://raw.githubusercontent.com/Xatta-Trone/google-scholar-scrapper/refs/heads/main/publications-U9tD0ywAAAAJ.tsv"

# Use the correct separator '\t' and handle errors gracefully
publications = pd.read_csv(
    file_path, sep="\t", encoding="utf-8", on_bad_lines="skip")

# Function to escape special characters for YAML
html_escape_table = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;"
}


def html_escape(text):
    """Escape special characters for YAML compatibility."""
    return "".join(html_escape_table.get(c, c) for c in str(text))


# Create Markdown files for each publication
output_folder = "../_publications/"
os.makedirs(output_folder, exist_ok=True)  # Ensure the directory exists

for index, item in publications.iterrows():
    # Generate filenames
    url_slug = item.get("url_slug", "").strip()
    pub_date = str(item.get("pub_date", "Unknown")).strip()
    if pub_date == "Unknown" or not url_slug:
        continue  # Skip entries with missing key information

    md_filename = f"{pub_date}-{url_slug}.md"
    html_filename = f"{pub_date}-{url_slug}"

    # Extract fields safely
    title = html_escape(item.get("title", "Untitled"))
    venue = html_escape(item.get("venue", "N/A"))
    excerpt = html_escape(item.get("excerpt", ""))
    citation = html_escape(item.get("citation", ""))
    paper_url = item.get("paper_url", "").strip()

    # Create the Markdown content
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

    # Add additional markdown content
    if paper_url:
        md += f"\n<a href='{paper_url}'>Download paper here</a>\n"

    if excerpt:
        md += f"\n{excerpt}\n"

    md += f"\nRecommended citation: {citation}"

    # Save the markdown file
    with open(os.path.join(output_folder, md_filename), "w", encoding="utf-8") as f:
        f.write(md)

print("✅ Markdown files generated successfully!")
