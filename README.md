# Font Checker

A lightweight web font auditing tool for license compliance and font inventory management. Extracts all fonts from websites—including custom fonts, web fonts, system fonts, and generic fallbacks—and exports detailed CSV reports.

## What It Does

Font Checker analyzes websites to identify every font that could potentially render, helping legal teams and developers audit font licensing. It uses Playwright to execute JavaScript on live pages, extracting computed font-family values and @font-face declarations that static HTML parsers often miss.

## Installation

```bash
pip install playwright
playwright install chromium
```

## Usage

### 1. Extract Fonts from a Website

```bash
python font_extractor.py https://example.com
```

**Output**: Creates `Results/example.com.csv` with columns:
- Font Name
- Type (Primary/Fallback/Generic/System)
- Format(s) (woff2, woff, ttf, etc.)
- Description *(empty - fill manually)*
- Source *(empty - fill manually)*
- Site

### 2. Merge Multiple Site Reports

```bash
python merge_csvs.py
```

**Output**: Creates `Results/all-sites.csv` consolidating all CSV files with:
- Automatic deduplication by font name
- Combined site lists (e.g., "site1.com, site2.com")
- Intelligent metadata merging

## Output

CSV reports include:
- **Primary fonts**: Custom @font-face declarations with format details
- **Fallback fonts**: System fonts specified in CSS
- **Generic fonts**: Keywords like sans-serif, monospace
- **File metadata**: Formats (woff2, woff, ttf) for license verification

## Using with Claude.ai

The Python scripts can be run directly for basic font extraction. For enhanced data collection (filling in Description and Source fields), use `FONT-CHECKER.md` with Claude.ai to automatically research and enrich font metadata via web search.
