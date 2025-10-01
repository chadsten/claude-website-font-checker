# Font Checker Instructions

## Purpose
This instruction set enables comprehensive font auditing for license review purposes. Use this to extract ALL fonts used on any website, including custom fonts, web fonts, system fonts, and generic font family keywords.

## Input Required
- **URL**: The website URL to audit for font usage

## Process

### Direct Playwright Extraction (Preferred Method)
Use the Python Playwright script at `browser_font_extractor.py` to extract all fonts:

1. **Run the extraction script**:
   ```bash
   python browser_font_extractor.py <URL>
   ```

2. The script will:
   - Navigate to the URL using a headless Chromium browser
   - Wait for the page to fully load (3 seconds)
   - Execute JavaScript to extract ALL fonts from:
     - Computed font-family values from all rendered DOM elements
     - @font-face declarations in all stylesheets
   - Parse font-family chains into individual font names
   - Generate a CSV file named `{domain}.csv`

3. **Automatic enrichment step**:
   - The CSV will be generated with empty Description and Source columns
   - **YOU (Claude) must automatically enrich each font**:
     - Use WebSearch to look up each font name (e.g., "Futura PT font")
     - If the top result is Adobe Fonts, Google Fonts, or another reputable foundry, add the link to the Source column
     - Add a brief description from the search results to the Description column
     - Update the CSV with proper source links and descriptions
     - For obscure/uncommon fonts, use "Custom Font" or brief description
   - Save the enriched CSV back to the file

**This method is reliable and works even when WebFetch fails due to bot protection.**

## Output Format

### Font Names List
Provide a simple bulleted list:
- One font name per line
- Alphabetically sorted
- Deduplicated (no repeats)
- No font-family chains, just individual font names

Example:
```
- Arial
- Georgia
- Helvetica Neue
- Inter
- monospace
- Roboto
- sans-serif
- serif
```

### Font Files (@font-face declarations)
When available, also provide details about actual font files:
- Font family name
- Format (woff, woff2, ttf, otf, etc.)
- File extension
- Source URL (for license verification)

Example:
```
Font Files (@font-face declarations):

- Font Awesome 5 Brands
  Format: woff2
  Extension: woff2
  URL: https://ka-f.fontawesome.com/releases/v5.15.2/webfonts/free-fa-brands-400.woff2

- Futura PT Medium
  Format: woff2
  Extension: woff2
  URL: FuturaPT-Medium.woff2

- Larken
  Format: woff
  Extension: woff
  URL: Larken-Medium.woff
```

## Restrictions
- **DO NOT** use curl for fetching
- **DO NOT** skip generic font keywords - include them all

## Notes
- This is for legal/license review purposes, so completeness is critical
- Include every font that could potentially be rendered
- Fallback fonts matter for license compliance
