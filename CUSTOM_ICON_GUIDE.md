# Custom Icon Setup Guide for Novel Scraper VBScript Launcher

## Overview
The VBScript launcher (`Novel Scraper GUI.vbs`) now supports custom icons for desktop shortcuts. This guide shows you how to set up your preferred icon.

## Quick Setup Steps

### 1. Get Your Icon File
- Find or create an icon file in `.ico` format
- You can convert images to .ico format using online converters like:
  - https://convertio.co/png-ico/
  - https://www.icoconverter.com/
  - https://favicon.io/favicon-converter/

### 2. Name Your Icon File
Place your icon file in the same folder as the VBScript with one of these names:
- `icon.ico` (recommended)
- `app_icon.ico`
- `novel_scraper.ico`
- `scraper.ico`

### 3. Create Desktop Shortcut
Run one of these methods:

**Method A: Use the batch file**
- Double-click `create_shortcut_with_icon.bat`

**Method B: Manual command**
- Open Command Prompt in the novel scraper folder
- Run: `wscript.exe "Novel Scraper GUI.vbs" /createshortcut`

## File Structure Example
```
your-novel-scraper-folder/
├── app_version_scrape_novel.py
├── Novel Scraper GUI.vbs
├── create_shortcut_with_icon.bat
├── icon.ico                    ← Your custom icon here
└── ... (other files)
```

## Icon Specifications
- **Format**: .ico file
- **Recommended sizes**: 16x16, 32x32, 48x48, 256x256 pixels
- **Max file size**: Keep under 1MB for best performance

## What Happens
1. The VBScript looks for icon files in this order:
   - icon.ico
   - app_icon.ico  
   - novel_scraper.ico
   - scraper.ico

2. If found, creates desktop shortcut with your custom icon
3. If not found, uses default Python icon
4. Shows confirmation message

## Troubleshooting
- **No icon shows**: Make sure the .ico file is in the correct folder with the right name
- **Wrong icon**: Delete the desktop shortcut and recreate it after fixing the icon file
- **Permission error**: Run as administrator if needed

## Icons You Can Use
Some good icon sources for novel/book apps:
- 📚 Book icons from Flaticon.com
- 📖 Reading icons from Icons8.com
- 🔖 Bookmark icons from Iconify.design
- Custom icons matching your app's theme

## Notes
- The VBScript still works normally for launching the app
- The `/createshortcut` parameter is only for creating desktop shortcuts
- You can recreate the shortcut anytime with a new icon
- Desktop shortcut will launch the app silently (no command window)
