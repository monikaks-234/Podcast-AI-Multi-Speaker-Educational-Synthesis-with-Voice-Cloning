"""
End-to-End Test Verification Script for AI Podcast Generation Platform
"""
import os
import sys

print("Testing core modules initialization...")

from core.rag_processor import DocumentProcessor
from core.script_generator import ScriptGenerator
from core.tts_engine import TTSEngine
from core.audio_mixer import AudioMixer
from core.local_video_renderer import LocalVideoRenderer
from core.evaluation_metrics import EvaluationMetrics

print("1. Testing Script Generator...")
script_gen = ScriptGenerator()
dialogue = script_gen.generate_script(
    topic="AI and Deep Learning Innovations",
    duration_minutes=0.5,
    podcast_style="Informative"
)
print(f"   Generated {len(dialogue)} dialogue turns.")
assert len(dialogue) > 0

print("2. Testing Edge-TTS Speech Synthesis...")
tts_engine = TTSEngine(output_dir="outputs")
segments = tts_engine.synthesize_podcast_dialogue_sync(dialogue[:3])
print(f"   Synthesized {len(segments)} audio segments.")
assert len(segments) == 3

print("3. Testing Audio Concatenation & Subtitles...")
audio_mixer = AudioMixer(output_dir="outputs")
master_audio = audio_mixer.concatenate_segments(segments, master_filename="test_master.mp3")
srt_path = audio_mixer.generate_srt_subtitles(segments, srt_filename="test_captions.srt")
print(f"   Master audio created: {os.path.exists(master_audio)}")
print(f"   Subtitles created: {os.path.exists(srt_path)}")
assert os.path.exists(master_audio)

print("4. Testing Local Video Renderer (CPU mode)...")
video_renderer = LocalVideoRenderer(output_dir="outputs", width=640, height=360, fps=15)
video_path = video_renderer.render_podcast_video(
    segments=segments,
    master_audio_path=master_audio,
    output_filename="test_podcast_studio.mp4",
    podcast_title="Test AI Podcast"
)
print(f"   Studio video rendered: {os.path.exists(video_path)}")
assert os.path.exists(video_path)

print("5. Testing Evaluation Metrics...")
metrics = EvaluationMetrics.analyze_script_metrics(dialogue)
print(f"   Metrics computed: Readability={metrics['flesch_reading_ease']}, Grade={metrics['flesch_kincaid_grade']}")

print("\n[SUCCESS] ALL CORE MODULE VERIFICATIONS PASSED SUCCESSFULLY!")
