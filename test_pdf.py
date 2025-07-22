"""
Simple test for the PDF formatter
"""

import os
import sys

def test_pdf_formatter():
    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    try:
        from format_novel_to_pdf import NovelPDFFormatter
        print("✅ PDF formatter imported successfully")
        
        formatter = NovelPDFFormatter()
        print("✅ PDF formatter initialized successfully")
        
        # Test getting novel chapters
        novel_folders = formatter.get_novel_chapters("chapters")
        print(f"✅ Found {len(novel_folders)} novel folders")
        
        for novel_name, chapters in novel_folders.items():
            print(f"   📚 {novel_name}: {len(chapters)} chapters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pdf_formatter()
