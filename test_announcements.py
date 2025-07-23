"""
Quick test for the new voice notification system
"""

# Import the functions from the main script
import sys
import os
sys.path.append(os.path.dirname(__file__))

from scrape_novel import announce_completion, speak_message

def test_announcements():
    print("Testing voice announcements...")
    print("=" * 50)
    
    # Test 1: Successful completion
    print("\n1. Testing successful completion announcement:")
    announce_completion(5, 5, success=True)
    
    input("Press Enter to continue to next test...")
    
    # Test 2: Partial completion
    print("\n2. Testing partial completion announcement:")
    announce_completion(3, 5, success=True)
    
    input("Press Enter to continue to next test...")
    
    # Test 3: Failed completion
    print("\n3. Testing failed completion announcement:")
    announce_completion(0, 5, success=False)
    
    input("Press Enter to continue to custom message test...")
    
    # Test 4: Custom message
    print("\n4. Testing custom message:")
    speak_message("This is a custom test message. The voice system is working perfectly!")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_announcements()
