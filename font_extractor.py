"""
Font extraction script using Playwright
Extracts all fonts from a webpage including computed styles
Outputs to CSV format with font details
"""

from playwright.sync_api import sync_playwright
import sys
import csv
import os
from urllib.parse import urlparse
from collections import defaultdict

def extract_fonts(url):
    fonts = set()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        print(f"Navigating to {url}...", file=sys.stderr)
        page.goto(url)
        page.wait_for_timeout(3000)  # Wait 3 seconds for page to load

        # JavaScript to extract all fonts with file information
        js_code = """
        () => {
            const fonts = new Set();
            const fontFiles = [];

            // Get all elements
            const allElements = document.querySelectorAll('*');

            // Extract computed font-family from each element
            allElements.forEach(element => {
                const computedStyle = window.getComputedStyle(element);
                const fontFamily = computedStyle.fontFamily;

                if (fontFamily) {
                    // Split by comma and clean up each font name
                    const fontList = fontFamily.split(',').map(font =>
                        font.trim().replace(/['"]/g, '')
                    );

                    fontList.forEach(font => {
                        if (font) fonts.add(font);
                    });
                }
            });

            // Extract @font-face declarations with source information
            for (const sheet of document.styleSheets) {
                try {
                    const rules = sheet.cssRules || sheet.rules;
                    if (rules) {
                        for (const rule of rules) {
                            if (rule.type === CSSRule.FONT_FACE_RULE) {
                                const fontFamily = rule.style.fontFamily;
                                const src = rule.style.src;

                                if (fontFamily) {
                                    const cleanFamily = fontFamily.replace(/['"]/g, '');
                                    fonts.add(cleanFamily);

                                    if (src) {
                                        // Extract URLs and formats from src
                                        const urlMatches = src.match(/url\(['"]?([^'"\\)]+)['"]?\)(?:\s+format\(['"]?([^'"\\)]+)['"]?\))?/g);
                                        if (urlMatches) {
                                            urlMatches.forEach(match => {
                                                const urlMatch = match.match(/url\(['"]?([^'"\\)]+)['"]?\)/);
                                                const formatMatch = match.match(/format\(['"]?([^'"\\)]+)['"]?\)/);

                                                if (urlMatch) {
                                                    fontFiles.push({
                                                        family: cleanFamily,
                                                        url: urlMatch[1],
                                                        format: formatMatch ? formatMatch[1] : 'unknown'
                                                    });
                                                }
                                            });
                                        }
                                    }
                                }
                            }
                        }
                    }
                } catch (e) {
                    // Cross-origin stylesheets may throw errors
                }
            }

            return {
                fonts: Array.from(fonts),
                fontFiles: fontFiles
            };
        }
        """

        # Execute JavaScript and get fonts
        result = page.evaluate(js_code)
        fonts.update(result['fonts'])
        font_files = result['fontFiles']

        browser.close()

    return sorted(fonts), font_files

def get_font_type(font_name, font_files_map):
    """Determine if font is Primary, Fallback, System, or Generic"""

    # Generic font families are always fallbacks
    generic_fonts = ['sans-serif', 'serif', 'monospace', 'cursive', 'fantasy', 'system-ui']
    if font_name in generic_fonts:
        return "Generic"

    # System fonts are fallbacks
    system_fonts = ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto',
                   'Helvetica Neue', 'Arial', 'Times New Roman', 'Georgia',
                   'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
                   'Noto Color Emoji', 'Noto Sans', 'Liberation Sans']
    if font_name in system_fonts:
        return "Fallback"

    # Fonts with @font-face declarations are primary
    if font_name in font_files_map:
        return "Primary"

    # Fonts without @font-face but in CSS are fallbacks
    return "Fallback"

def get_font_metadata(font_name, font_files_map):
    """Get basic metadata - descriptions and sources to be filled in manually"""

    # Get formats from @font-face declarations
    formats = set()
    if font_name in font_files_map:
        for file_info in font_files_map[font_name]:
            formats.add(file_info['format'])

    formats_str = ", ".join(sorted(formats)) if formats else "N/A"

    # Return empty placeholders - to be researched manually
    return {
        "description": "",
        "source": "",
        "formats": formats_str
    }

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://agent.bkvenergy.com"

    print(f"Extracting fonts from: {url}", file=sys.stderr)
    fonts, font_files = extract_fonts(url)

    # Create a map of font families to their file info
    font_files_map = defaultdict(list)
    for file_info in font_files:
        font_files_map[file_info['family']].append(file_info)

    # Get domain name for CSV filename
    domain = urlparse(url).netloc.replace('www.', '')

    # Create Results folder if it doesn't exist
    results_dir = "Results"
    os.makedirs(results_dir, exist_ok=True)

    csv_filename = os.path.join(results_dir, f"{domain}.csv")

    # Write to CSV
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Font Name', 'Type', 'Format(s)', 'Description', 'Source', 'Site']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for font in fonts:
            metadata = get_font_metadata(font, font_files_map)
            font_type = get_font_type(font, font_files_map)
            writer.writerow({
                'Font Name': font,
                'Type': font_type,
                'Format(s)': metadata['formats'],
                'Description': metadata['description'],
                'Source': metadata['source'],
                'Site': domain
            })

    print(f"\n✓ Font audit complete!", file=sys.stderr)
    print(f"✓ Results saved to: {csv_filename}", file=sys.stderr)
    print(f"✓ Total fonts found: {len(fonts)}", file=sys.stderr)
