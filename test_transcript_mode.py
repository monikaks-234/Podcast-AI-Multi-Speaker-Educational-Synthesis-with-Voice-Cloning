import os
import asyncio
from core.rag_processor import DocumentProcessor
from core.tts_engine import TTSEngine
from core.audio_mixer import AudioMixer

def test_teams_transcript_synthesis():
    sample_text = """
Anirban Dasgupta
0 minutes 4 seconds0:04
Anirban Dasgupta 0 minutes 4 seconds
All those things are pending, and I've also started my Capstone Two; we have discussed the idea with, like, what this is?

Dr. Shinu Abhi
0 minutes 17 seconds0:17
Dr. Shinu Abhi 0 minutes 17 seconds
Doctor Soumya, Soumya Mehdi, you forgot his name, huh?

Santosh Kumar Singh
1 hour 27 minutes 18 seconds1:27:18
Santosh Kumar Singh 1 hour 27 minutes 18 seconds
Yeah, ma'am, actually I have not started, but I made the first slide. So I'm going through all those tools which you are saying in the call.
"""

    temp_txt_path = "outputs/test_teams_transcript.txt"
    os.makedirs("outputs", exist_ok=True)
    with open(temp_txt_path, "w", encoding="utf-8") as f:
        f.write(sample_text)

    print("1. Parsing MS Teams Transcript...")
    turns, unique_speakers = DocumentProcessor.parse_meeting_transcript(temp_txt_path)
    print(f"   Detected {len(unique_speakers)} Unique Speakers: {unique_speakers}")
    print(f"   Extracted {len(turns)} Dialogue Turns without skipping.")

    print("2. Synthesizing Multi-Speaker Audio with Dynamic Neural Voices...")
    tts = TTSEngine(output_dir="outputs")
    segments = tts.synthesize_podcast_dialogue_sync(turns)
    print(f"   Synthesized {len(segments)} audio segments.")

    print("3. Concatenating Audio Track & Generating SRT Captions...")
    mixer = AudioMixer(output_dir="outputs")
    master_audio = mixer.concatenate_segments(segments, master_filename="test_transcript_master.mp3")
    srt_path = mixer.generate_srt_subtitles(segments, srt_filename="test_transcript_captions.srt")

    print(f"   Master Audio File: {master_audio} (Exists: {os.path.exists(master_audio)})")
    print(f"   Subtitles File: {srt_path} (Exists: {os.path.exists(srt_path)})")
    print("\n[SUCCESS] MS TEAMS TRANSCRIPT MODE VERIFICATION COMPLETE!")

if __name__ == "__main__":
    test_teams_transcript_synthesis()
