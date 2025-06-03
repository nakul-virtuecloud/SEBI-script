# SEBI Mutual Fund PDF Downloader

This RPA (Robotic Process Automation) tool automatically downloads KIM (Key Information Memorandum) and SID (Scheme Information Document) PDFs from the SEBI website.

## Features

- Downloads all KIM and SID PDFs from the SEBI website
- Handles dynamic website navigation
- Uses both Selenium for browser automation and direct requests for downloading
- Saves PDFs with descriptive filenames

## Installation

1. Install the required dependencies:

```bash
pip install selenium requests
```

2. Make sure you have Chrome browser installed

## Usage

To download all KIM and SID PDFs from the SEBI website:

```bash
python download_all_sebi_pdfs.py
```

## How It Works

The script:

1. Navigates to the KIM and SID listing pages on the SEBI website
2. Finds all fund links on each page
3. Visits each fund's details page
4. Downloads PDFs using two methods:
   - Direct download for PDF links
   - Browser automation for links that require JavaScript interaction
5. Saves all PDFs to the "downloads" folder

## Troubleshooting

If you encounter issues:

- Make sure your internet connection is stable
- Try running the script with a VPN if you're getting blocked
- Increase the wait times in the code if pages are loading slowly
- Check if the SEBI website structure has changed