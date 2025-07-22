"""
Novel Chapter to PDF Formatter
Converts scraped novel chapters to beautifully formatted PDF files

run using this command:
& "E:/VSCODE/scraping novel/.venv/Scripts/python.exe" "e:\VSCODE\scraping novel\format_novel_to_pdf.py"
"""

import os
import glob
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import black, darkblue, grey
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import datetime

class NovelPDFFormatter:
    def __init__(self):
        self.setup_styles()
        
    def setup_styles(self):
        """Setup custom styles for the PDF"""
        self.styles = getSampleStyleSheet()
        
        # Custom title style
        self.title_style = ParagraphStyle(
            'NovelTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            spaceBefore=30,
            alignment=TA_CENTER,
            textColor=darkblue,
            fontName='Helvetica-Bold'
        )
        
        # Chapter title style
        self.chapter_title_style = ParagraphStyle(
            'ChapterTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            spaceBefore=30,
            alignment=TA_CENTER,
            textColor=darkblue,
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            spaceBefore=10,
            alignment=TA_CENTER,
            textColor=grey,
            fontName='Helvetica-Oblique'
        )
        
        # Body text style
        self.body_style = ParagraphStyle(
            'NovelBody',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=12,
            spaceBefore=6,
            alignment=TA_JUSTIFY,
            leftIndent=0,
            rightIndent=0,
            fontName='Helvetica',
            leading=18  # Line spacing
        )
        
        # Dialog style (for quoted text)
        self.dialog_style = ParagraphStyle(
            'Dialog',
            parent=self.body_style,
            leftIndent=20,
            rightIndent=20,
            fontName='Helvetica-Oblique',
            textColor=colors.darkslategray
        )
        
        # System message style (for game-like elements)
        self.system_style = ParagraphStyle(
            'SystemMessage',
            parent=self.body_style,
            leftIndent=30,
            rightIndent=30,
            fontSize=11,
            fontName='Courier',
            textColor=colors.darkgreen,
            backColor=colors.lightgrey,
            borderColor=colors.darkgreen,
            borderWidth=1,
            borderPadding=5
        )

    def clean_title(self, title):
        """Clean and format the title"""
        # Remove website branding
        title = re.sub(r'–\s*☕\s*Kat Reading Cafe.*$', '', title)
        title = re.sub(r'- Read.*Online.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'#Chapter\s*\d+\s*', '', title)
        
        # Clean up extra spaces and dashes
        title = re.sub(r'\s*–\s*', ' – ', title)
        title = re.sub(r'\s+', ' ', title).strip()
        
        return title

    def parse_chapter_content(self, content):
        """Parse chapter content and identify different text types"""
        lines = content.split('\n')
        parsed_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect system messages (surrounded by brackets or special formatting)
            if (line.startswith('【') and line.endswith('】')) or \
               (line.startswith('[') and line.endswith(']')) or \
               ('System' in line and any(char in line for char in ['【', '[', '『'])):
                parsed_content.append(('system', line))
            
            # Detect dialog (lines with quotes)
            elif ('"' in line and line.count('"') >= 2) or \
                 (line.startswith('"') or line.endswith('"')) or \
                 ('said' in line.lower() or 'asked' in line.lower()):
                parsed_content.append(('dialog', line))
            
            # Regular body text
            else:
                parsed_content.append(('body', line))
                
        return parsed_content

    def create_chapter_pdf(self, chapter_files, novel_name, output_path):
        """Create a PDF from multiple chapter files"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2.5*cm,
            bottomMargin=2*cm,
            title=f"{novel_name} - Chapters"
        )
        
        story = []
        
        # Add title page
        story.append(Paragraph(novel_name, self.title_style))
        story.append(Spacer(1, 20))
        
        # Add subtitle with chapter range
        if chapter_files:
            first_chapter = self.extract_chapter_number(chapter_files[0])
            last_chapter = self.extract_chapter_number(chapter_files[-1])
            subtitle = f"Chapters {first_chapter} - {last_chapter}"
            story.append(Paragraph(subtitle, self.subtitle_style))
        
        story.append(Spacer(1, 30))
        
        # Add generation info
        generation_info = f"Generated on {datetime.datetime.now().strftime('%B %d, %Y')}"
        story.append(Paragraph(generation_info, self.subtitle_style))
        
        story.append(PageBreak())
        
        # Process each chapter
        for i, chapter_file in enumerate(chapter_files):
            print(f"📖 Processing: {os.path.basename(chapter_file)}")
            
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split title and content
            lines = content.split('\n', 1)
            title = self.clean_title(lines[0]) if lines else "Chapter"
            chapter_content = lines[1] if len(lines) > 1 else ""
            
            # Add chapter title
            story.append(Paragraph(title, self.chapter_title_style))
            story.append(Spacer(1, 20))
            
            # Parse and add content
            parsed_content = self.parse_chapter_content(chapter_content)
            
            for content_type, text in parsed_content:
                if content_type == 'system':
                    story.append(Paragraph(text, self.system_style))
                elif content_type == 'dialog':
                    story.append(Paragraph(text, self.dialog_style))
                else:
                    story.append(Paragraph(text, self.body_style))
                
                story.append(Spacer(1, 6))
            
            # Add page break between chapters (except for the last one)
            if i < len(chapter_files) - 1:
                story.append(PageBreak())
        
        # Build the PDF
        doc.build(story)
        print(f"✅ PDF created: {output_path}")

    def extract_chapter_number(self, filename):
        """Extract chapter number from filename"""
        match = re.search(r'^(\d+)_', os.path.basename(filename))
        return int(match.group(1)) if match else 0

    def get_novel_chapters(self, chapters_dir):
        """Get all novel folders and their chapters"""
        novel_folders = {}
        
        if not os.path.exists(chapters_dir):
            print(f"❌ Chapters directory not found: {chapters_dir}")
            return novel_folders
        
        for item in os.listdir(chapters_dir):
            folder_path = os.path.join(chapters_dir, item)
            if os.path.isdir(folder_path):
                # Get all .txt files in the folder
                txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
                if txt_files:
                    # Sort by chapter number
                    txt_files.sort(key=self.extract_chapter_number)
                    novel_folders[item] = txt_files
        
        return novel_folders

    def select_chapters_range(self, chapter_files):
        """Let user select which chapters to include in PDF"""
        if not chapter_files:
            return []
        
        print(f"\n📚 Found {len(chapter_files)} chapters")
        print("📋 Available chapters:")
        
        for i, file in enumerate(chapter_files[:10]):  # Show first 10
            chapter_num = self.extract_chapter_number(file)
            filename = os.path.basename(file)
            # Truncate long filenames
            display_name = filename if len(filename) <= 60 else filename[:57] + "..."
            print(f"   {chapter_num:3d}. {display_name}")
        
        if len(chapter_files) > 10:
            print(f"   ... and {len(chapter_files) - 10} more chapters")
        
        print(f"\n📊 Chapter range: {self.extract_chapter_number(chapter_files[0])} - {self.extract_chapter_number(chapter_files[-1])}")
        
        while True:
            try:
                choice = input("\n🔢 Select range:\n  1. All chapters\n  2. Custom range\n  3. Latest N chapters\nChoice (1-3): ").strip()
                
                if choice == "1":
                    return chapter_files
                
                elif choice == "2":
                    start = int(input("Start chapter number: "))
                    end = int(input("End chapter number: "))
                    
                    selected = []
                    for file in chapter_files:
                        chapter_num = self.extract_chapter_number(file)
                        if start <= chapter_num <= end:
                            selected.append(file)
                    
                    if selected:
                        print(f"✅ Selected {len(selected)} chapters ({start}-{end})")
                        return selected
                    else:
                        print("❌ No chapters found in that range")
                        continue
                
                elif choice == "3":
                    n = int(input("How many latest chapters: "))
                    if n > 0:
                        selected = chapter_files[-n:] if n <= len(chapter_files) else chapter_files
                        print(f"✅ Selected latest {len(selected)} chapters")
                        return selected
                    else:
                        print("❌ Please enter a positive number")
                        continue
                
                else:
                    print("❌ Please enter 1, 2, or 3")
                    continue
                    
            except ValueError:
                print("❌ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n👋 Cancelled!")
                return []

def main():
    """Main execution function"""
    formatter = NovelPDFFormatter()
    
    # Configuration
    chapters_dir = "chapters"
    output_dir = "pdf_novels"
    
    print("📚 Novel to PDF Converter")
    print("=" * 40)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get available novels
    novel_folders = formatter.get_novel_chapters(chapters_dir)
    
    if not novel_folders:
        print("❌ No novel folders found in chapters directory")
        return
    
    # Display available novels
    print("\n📖 Available novels:")
    novel_list = list(novel_folders.keys())
    for i, novel_name in enumerate(novel_list, 1):
        chapter_count = len(novel_folders[novel_name])
        display_name = novel_name.replace('-', ' ').title()
        print(f"   {i}. {display_name} ({chapter_count} chapters)")
    
    # Let user select novel
    while True:
        try:
            choice = input(f"\n🔢 Select novel (1-{len(novel_list)}): ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(novel_list):
                selected_novel = novel_list[choice_num - 1]
                break
            else:
                print(f"❌ Please enter a number between 1 and {len(novel_list)}")
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            return
    
    # Get chapter files for selected novel
    chapter_files = novel_folders[selected_novel]
    
    # Let user select chapter range
    selected_chapters = formatter.select_chapters_range(chapter_files)
    if not selected_chapters:
        print("❌ No chapters selected")
        return
    
    # Generate output filename
    novel_display_name = selected_novel.replace('-', ' ').title()
    first_chapter = formatter.extract_chapter_number(selected_chapters[0])
    last_chapter = formatter.extract_chapter_number(selected_chapters[-1])
    
    if len(selected_chapters) == 1:
        output_filename = f"{novel_display_name} - Chapter {first_chapter}.pdf"
    else:
        output_filename = f"{novel_display_name} - Chapters {first_chapter}-{last_chapter}.pdf"
    
    output_path = os.path.join(output_dir, output_filename)
    
    print(f"\n🎯 Creating PDF: {output_filename}")
    print(f"📁 Output path: {output_path}")
    print(f"📖 Processing {len(selected_chapters)} chapters...")
    
    try:
        # Create the PDF
        formatter.create_chapter_pdf(selected_chapters, novel_display_name, output_path)
        
        print(f"\n🎉 Success! PDF created successfully!")
        print(f"📁 Saved to: {output_path}")
        print(f"📊 Contains {len(selected_chapters)} chapters")
        
        # Ask if user wants to open the PDF
        try:
            open_pdf = input("\n📖 Open PDF now? (y/n): ").strip().lower()
            if open_pdf in ['y', 'yes']:
                os.startfile(output_path)  # Windows
        except:
            pass
            
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
