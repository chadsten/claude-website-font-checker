#!/usr/bin/env python3
"""
CSV Merger for Font Checker Results

This script merges all CSV files from the Results/ folder (or current directory)
into a single consolidated CSV file with an added 'Site' column.

Features:
- Deduplicates fonts by Font Name
- Combines sites into comma-separated lists (e.g., "bkv.com, agent.bkvenergy.com")
- Intelligently merges metadata fields (Type, Format(s), Description, Source)
- Preserves all existing functionality (error handling, encoding fallback, progress reporting)

Author: Generated for font-checker project
"""

import csv
import glob
import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple


def find_csv_files(results_dir: str, output_filename: str) -> List[str]:
    """
    Find all CSV files in the specified directory, excluding the output file.

    Args:
        results_dir: Directory to search for CSV files
        output_filename: Name of the output file to exclude

    Returns:
        List of CSV file paths
    """
    # Search for CSV files
    search_pattern = os.path.join(results_dir, "*.csv")
    csv_files = glob.glob(search_pattern)

    # Exclude the output file itself to avoid recursion
    output_path = os.path.join(results_dir, output_filename)
    csv_files = [f for f in csv_files if os.path.abspath(f) != os.path.abspath(output_path)]

    return sorted(csv_files)


def extract_site_name(filepath: str) -> str:
    """
    Extract site name from the CSV filename.

    Args:
        filepath: Full path to the CSV file

    Returns:
        Site name (filename without extension)
    """
    return Path(filepath).stem


def read_csv_with_fallback(filepath: str) -> Tuple[List[str], List[List[str]]]:
    """
    Read a CSV file with encoding fallback handling.

    Args:
        filepath: Path to the CSV file

    Returns:
        Tuple of (headers, rows)
    """
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']

    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding, newline='') as f:
                reader = csv.reader(f)
                rows = list(reader)

                if not rows:
                    return [], []

                # First non-empty row is the header
                headers = rows[0] if rows else []
                data_rows = rows[1:] if len(rows) > 1 else []

                # Filter out empty rows
                data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]

                return headers, data_rows

        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"  Warning: Error reading {filepath} with {encoding}: {e}")
            continue

    print(f"  Error: Could not read {filepath} with any encoding")
    return [], []


def select_best_value(values: List[str]) -> str:
    """
    Select the best value from a list of potential values.
    Prefers non-empty, more detailed values.

    Args:
        values: List of values to choose from

    Returns:
        The best value (most complete/detailed)
    """
    # Filter out empty strings
    non_empty = [v.strip() for v in values if v and v.strip()]

    if not non_empty:
        return ""

    # Return the longest non-empty value (likely most detailed)
    return max(non_empty, key=len)


def deduplicate_fonts(all_rows: List[List[str]]) -> List[List[str]]:
    """
    Deduplicate fonts by Font Name, combining sites into comma-separated lists.

    Args:
        all_rows: List of rows, each containing [Font Name, Type, Format(s), Description, Source, Site]

    Returns:
        Deduplicated list of rows with combined sites
    """
    # Dictionary to collect font data: font_name -> list of row data
    fonts_dict: Dict[str, List[List[str]]] = {}

    for row in all_rows:
        if not row or len(row) < 6:
            continue

        font_name = row[0].strip()
        if not font_name:
            continue

        if font_name not in fonts_dict:
            fonts_dict[font_name] = []

        fonts_dict[font_name].append(row)

    # Merge duplicate fonts
    deduplicated_rows = []

    for font_name, rows in sorted(fonts_dict.items()):
        # Collect all sites for this font
        sites = []
        for row in rows:
            site = row[5].strip() if len(row) > 5 else ""
            if site:
                sites.append(site)

        # Remove duplicate sites while preserving order
        unique_sites = []
        seen = set()
        for site in sites:
            if site not in seen:
                unique_sites.append(site)
                seen.add(site)

        # Combine sites into comma-separated string
        combined_sites = ", ".join(unique_sites)

        # Merge metadata fields (Type, Format(s), Description, Source)
        type_values = [row[1] for row in rows if len(row) > 1]
        format_values = [row[2] for row in rows if len(row) > 2]
        description_values = [row[3] for row in rows if len(row) > 3]
        source_values = [row[4] for row in rows if len(row) > 4]

        merged_row = [
            font_name,
            select_best_value(type_values),
            select_best_value(format_values),
            select_best_value(description_values),
            select_best_value(source_values),
            combined_sites
        ]

        deduplicated_rows.append(merged_row)

    return deduplicated_rows


def merge_csv_files(results_dir: str = "Results", output_filename: str = "all-sites.csv") -> None:
    """
    Merge all CSV files in the Results directory into a single file with deduplication.

    Fonts are deduplicated by Font Name, with sites combined into comma-separated lists.

    Args:
        results_dir: Directory containing CSV files to merge
        output_filename: Name of the output merged file
    """
    print(f"Font CSV Merger (with Deduplication)")
    print("=" * 70)

    # Check if Results directory exists, fallback to current directory
    if not os.path.exists(results_dir):
        print(f"Warning: '{results_dir}' directory not found. Using current directory.")
        results_dir = "."

    # Find all CSV files
    csv_files = find_csv_files(results_dir, output_filename)

    if not csv_files:
        print(f"\nNo CSV files found in '{results_dir}/'")
        return

    print(f"\nFound {len(csv_files)} CSV file(s) to merge:")
    for csv_file in csv_files:
        print(f"  - {os.path.basename(csv_file)}")

    # Expected headers (the Site column may or may not exist)
    expected_headers_without_site = ["Font Name", "Type", "Format(s)", "Description", "Source"]
    expected_headers_with_site = expected_headers_without_site + ["Site"]
    output_headers = expected_headers_with_site

    # Collect all data
    all_rows = []
    total_fonts_before_dedup = 0
    sites_processed = 0

    print(f"\nProcessing files...")
    print("-" * 70)

    for csv_file in csv_files:
        site_name = extract_site_name(csv_file)
        print(f"\nProcessing: {os.path.basename(csv_file)}")
        print(f"  Site: {site_name}")

        headers, rows = read_csv_with_fallback(csv_file)

        if not headers:
            print(f"  Skipped: Empty or unreadable file")
            continue

        # Check if Site column already exists
        has_site_column = (headers == expected_headers_with_site)

        # Validate headers
        if headers == expected_headers_with_site:
            print(f"  Headers: OK (includes Site column)")
        elif headers == expected_headers_without_site:
            print(f"  Headers: OK (will add Site column)")
        else:
            print(f"  Warning: Unexpected header format!")
            print(f"    Expected: {expected_headers_without_site} or {expected_headers_with_site}")
            print(f"    Found: {headers}")
            print(f"  Attempting to proceed anyway...")

        if not rows:
            print(f"  Skipped: No data rows found")
            continue

        # Process each row
        for row in rows:
            if has_site_column:
                # CSV already has Site column - ensure correct number of columns
                while len(row) < len(expected_headers_with_site):
                    row.append("")
                row_with_site = row[:len(expected_headers_with_site)]

            else:
                # CSV doesn't have Site column - add it
                # Ensure row has correct number of columns (pad if necessary)
                while len(row) < len(expected_headers_without_site):
                    row.append("")

                # Add site name as the last column
                row_with_site = row[:len(expected_headers_without_site)] + [site_name]

            all_rows.append(row_with_site)

        print(f"  Added: {len(rows)} font(s)")
        total_fonts_before_dedup += len(rows)
        sites_processed += 1

    # Deduplicate fonts
    if not all_rows:
        print(f"\nNo data to merge!")
        return

    print("\n" + "-" * 70)
    print(f"Deduplicating fonts...")
    deduplicated_rows = deduplicate_fonts(all_rows)
    duplicates_removed = total_fonts_before_dedup - len(deduplicated_rows)
    print(f"  Before deduplication: {total_fonts_before_dedup} font entries")
    print(f"  After deduplication: {len(deduplicated_rows)} unique fonts")
    print(f"  Duplicates removed: {duplicates_removed}")

    # Write merged CSV
    output_path = os.path.join(results_dir, output_filename)

    try:
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(output_headers)
            writer.writerows(deduplicated_rows)

        print("\n" + "=" * 70)
        print(f"SUCCESS: Merged CSV created!")
        print("=" * 70)
        print(f"Output file: {os.path.abspath(output_path)}")
        print(f"Unique fonts: {len(deduplicated_rows)}")
        print(f"Sites processed: {sites_processed}")
        print(f"Columns: {', '.join(output_headers)}")

        # Calculate file size
        file_size = os.path.getsize(output_path)
        if file_size < 1024:
            size_str = f"{file_size} bytes"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.2f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.2f} MB"

        print(f"Output file size: {size_str}")

    except Exception as e:
        print(f"\nError writing output file: {e}")
        sys.exit(1)


def main():
    """Main entry point for the script."""
    # You can customize these parameters
    results_dir = "Results"
    output_filename = "all-sites.csv"

    try:
        merge_csv_files(results_dir, output_filename)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
