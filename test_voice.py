"""
Test script for voice notifications
Run this to test if voice notifications work on your system
"""

def test_voice():
    print("Testing voice notification system...")
    
    # Test Windows SAPI first
    try:
        import win32com.client
        print("✅ Windows SAPI available")
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        speaker.Speak("Hello! This is a test of the Windows speech system.")
        return True
    except Exception as e:
        print(f"❌ Windows SAPI failed: {e}")
    
    # Test pyttsx3
    try:
        import pyttsx3
        print("✅ pyttsx3 available")
        engine = pyttsx3.init()
        engine.say("Hello! This is a test of the pyttsx3 speech system.")
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"❌ pyttsx3 failed: {e}")
    
    # Test PowerShell
    try:
        import subprocess
        print("✅ Testing PowerShell TTS...")
        ps_command = '''
        Add-Type -AssemblyName System.Speech;
        $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
        $synth.Speak("Hello! This is a test of PowerShell speech system.");
        '''
        subprocess.run(['powershell', '-Command', ps_command], 
                      capture_output=True, timeout=10)
        print("✅ PowerShell TTS works")
        return True
    except Exception as e:
        print(f"❌ PowerShell TTS failed: {e}")
    
    print("❌ No TTS system available")
    return False

if __name__ == "__main__":
    print("🎙️ Voice Notification Test")
    print("=" * 50)
    
    if test_voice():
        print("\n✅ Voice notifications should work!")
        print("You can now run the novel scraper with voice announcements.")
    else:
        print("\n❌ Voice notifications not available.")
        print("Run 'install_tts.bat' to install required packages.")
    
    input("\nPress Enter to exit...")
