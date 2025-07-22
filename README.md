# Novel Scraper & PDF Formatter

A comprehensive toolkit for downloading web novels and converting them to beautifully formatted PDF files.

## 📚 Features

### Novel Scraper (`scrape_novel.py`)
- **Multi-website support**: KatReadingCafe and NovelBin
- **Smart resuming**: Automatically continues from where you left off
- **Anti-detection**: Uses fresh browser instances for NovelBin to avoid blocking
- **Batch downloading**: Download 1-50 chapters at once
- **Safe file naming**: Handles special characters and long titles
- **Progress tracking**: Clear progress indicators and chapter counting

### PDF Formatter (`format_novel_to_pdf.py`)
- **Professional formatting**: Clean, readable PDF layout
- **Smart content detection**: Automatically formats dialog, system messages, and body text
- **Flexible chapter selection**: All chapters, custom ranges, or latest N chapters
- **Beautiful styling**: Title pages, proper spacing, and typography
- **Batch processing**: Convert multiple chapters into single PDF files

## 🛠️ Installation

### Prerequisites
- **Python 3.7+**: [Download Python](https://www.python.org/downloads/)
- **Google Chrome**: Required for web scraping
- **ChromeDriver**: Will be automatically managed

### Setup Steps

1. **Clone or download this repository**
   ```bash
   git clone <your-repo-url>
   cd scraping-novel
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python scrape_novel.py --help
   ```

## 📖 Usage Guide

### 1. Setting Up Novel URLs

Create a `novel_urls.txt` file with your novel URLs (one per line):

```text
# KatReadingCafe novels
https://katreadingcafe.com/manga/genderswap-reincarnation-i-raised-the-strongest-player/

# NovelBin novels  
https://novelbin.me/book/seizing-destiny-from-heavens-hands

# Lines starting with # are comments and will be ignored
```

### 2. Downloading Novels

```bash
python scrape_novel.py
```

**Interactive Process:**
1. Select which novel to download from your list
2. Choose how many chapters to download (1-50)
3. The script will automatically:
   - Resume from where you left off
   - Handle different website structures
   - Use appropriate anti-detection measures
   - Save chapters with organized filenames

**Example Output:**
```
📚 Available novels:
   1. Genderswap Reincarnation I Raised The Strongest Player (KatReadingCafe)
   2. Seizing Destiny From Heavens Hands (NovelBin)

🔢 Select novel to download (1-2): 1
✅ Selected: Genderswap Reincarnation I Raised The Strongest Player
🌐 Website: katreadingcafe
📁 Will save to: chapters/genderswap-reincarnation-i-raised-the-strongest-player/

📚 How many chapters do you want to download? (1-50): 5
✅ Will download 5 chapters

📁 Found 9 existing chapters
🚀 Will download chapters 10 to 14
```

### 3. Converting to PDF

```bash
python format_novel_to_pdf.py
```

**Interactive Process:**
1. Select which novel to convert
2. Choose chapter range:
   - **All chapters**: Convert everything
   - **Custom range**: Specify start and end chapters
   - **Latest N chapters**: Get the most recent chapters
3. PDF will be generated with professional formatting

### 4. Website-Specific Behavior

#### KatReadingCafe
- Uses single browser session for efficiency
- Handles volume expansion automatically
- Optimized for bulk downloads

#### NovelBin
- **Fresh browser for each chapter** to avoid detection
- Automatic breaks between downloads (10-20 seconds)
- More resilient against anti-bot measures

## 📁 File Structure

```
scraping-novel/
├── scrape_novel.py              # Main scraping script
├── format_novel_to_pdf.py       # PDF conversion tool
├── novel_urls.txt               # Your novel URLs (create this)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── .venv/                       # Virtual environment (auto-created)
├── chapters/                    # Downloaded chapters
│   ├── novel-name-1/
│   │   ├── 001_Chapter Title.txt
│   │   ├── 002_Chapter Title.txt
│   │   └── ...
│   └── novel-name-2/
│       └── ...
└── pdf_novels/                  # Generated PDF files
    ├── Novel Name - Chapters 1-10.pdf
    └── Novel Name - Chapter 15.pdf
```

## 🎨 PDF Output Features

### Styling
- **Title Page**: Novel name, chapter range, generation date
- **Chapter Headers**: Clear chapter titles with proper spacing
- **Body Text**: Justified text with comfortable line spacing
- **Dialog**: Italicized and indented for easy reading
- **System Messages**: Special formatting for game-like elements
- **Professional Layout**: A4 size with proper margins

### Content Detection
The PDF formatter automatically detects and styles:
- Regular narrative text
- Character dialog (quoted text)
- System messages (bracketed text like 【System】)
- Chapter titles and subtitles

## ⚙️ Configuration Options

### Chrome Driver Options
The scraper uses optimized Chrome settings:
- Headless mode (no visible browser window)
- Disabled images for faster loading
- Anti-detection measures
- Custom user agent

### File Naming
- Chapters are numbered with zero-padding (001, 002, etc.)
- Special characters are automatically cleaned
- Long titles are truncated safely
- Fallback naming for problematic titles

## 🔧 Troubleshooting

### Common Issues

#### Chrome Driver Problems
```
❌ Failed to start ChromeDriver
```
**Solutions:**
1. Ensure Chrome browser is installed
2. Try: `pip install webdriver-manager`
3. Download chromedriver.exe manually and place in project folder

#### No Chapters Found
```
❌ No chapters found in that range
```
**Causes:**
- Novel doesn't have chapters in the specified range
- Website structure changed
- Network connectivity issues

#### PDF Generation Errors
```
❌ Error creating PDF: ...
```
**Solutions:**
1. Ensure ReportLab is installed: `pip install reportlab`
2. Check if chapter files exist in chapters/ folder
3. Verify file permissions

### Debugging Tips

1. **Check chapter files**: Look in `chapters/[novel-name]/` for downloaded content
2. **Test single chapter**: Try downloading just 1 chapter first
3. **Check URLs**: Ensure URLs in `novel_urls.txt` are correct and accessible
4. **Monitor output**: The script provides detailed progress information

## 📊 Performance Notes

### Download Speed
- **KatReadingCafe**: ~2-3 seconds per chapter
- **NovelBin**: ~15-25 seconds per chapter (includes anti-detection delays)

### PDF Generation
- ~50-100 chapters per minute depending on content length
- Memory usage scales with number of chapters being processed

## 🤝 Contributing

Feel free to:
- Report bugs or issues
- Suggest new features
- Add support for additional websites
- Improve the PDF formatting

## ⚠️ Legal Notice

This tool is for personal use only. Please:
- Respect website terms of service
- Don't overload servers with excessive requests
- Support authors by purchasing official releases when available
- Use responsibly and ethically

## 📝 Version History

- **v1.0**: Initial release with KatReadingCafe and NovelBin support
- **v1.1**: Added PDF formatter with professional styling
- **v1.2**: Improved anti-detection for NovelBin with fresh browser instances
