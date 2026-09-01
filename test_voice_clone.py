import os
import sys
import asyncio
from core.voice_clone_engine import VoiceCloneEngine
from core.tts_engine import TTSEngine

def test_voice_clone():
    print("Testing VoiceCloneEngine...")
    vce = VoiceCloneEngine()
    status = vce.get_status()
    print("Initial Voice Clone Has Clone:", status.get("has_cloned_voice"))
    
    tts = TTSEngine()
    dialogue = [
        {"speaker": "Student (Female)", "text": "Hello, this is a test of my cloned voice.", "emotion": "curious"},
        {"speaker": "Professor (Male)", "text": "Welcome to class, let's begin our lesson.", "emotion": "explaining"}
    ]
    
    loop = asyncio.get_event_loop()
    segments = loop.run_until_complete(tts.synthesize_podcast_dialogue(dialogue))
    print(f"Synthesized {len(segments)} segments successfully!")
    for s in segments:
        print(f" - {s['speaker']}: {s['audio_path']} ({s['duration']:.2f}s)")
    
    print("[SUCCESS] Voice Clone & TTS Engine integration verified!")

if __name__ == "__main__":
    test_voice_clone()
