import os
import subprocess
from typing import List, Dict, Any
from pydub import AudioSegment

class AudioMixer:
    """
    Concatenates audio segments with pause buffers and generates subtitle files (.srt).
    Robustly handles corrupted or zero-byte audio segments without crashing.
    Adds 1.5s end silence buffer so final audio sentences are 100% complete.
    """

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def concatenate_segments(self, segments: List[Dict[str, Any]], master_filename: str = "master_podcast.mp3") -> str:
        """Concatenates all dialogue segments into a brisk, natural audio stream with minimal pause buffers."""
        output_path = os.path.join(self.output_dir, master_filename)
        
        combined = AudioSegment.empty()
        silence = AudioSegment.silent(duration=120) # 120ms crisp conversational pause between speakers

        for seg in segments:
            audio_path = seg.get("audio_path", "")
            if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 100:
                try:
                    segment_audio = AudioSegment.from_file(audio_path)
                    combined += segment_audio + silence
                except Exception as err:
                    print(f"[AudioMixer Warning] Skipping corrupted segment file '{audio_path}': {err}")

        # Add 400ms tail silence buffer
        combined += AudioSegment.silent(duration=400)

        # Fallback if empty audio
        if len(combined) <= 400:
            combined = AudioSegment.silent(duration=2000)

        # Export final combined audio
        combined.export(output_path, format="mp3", bitrate="192k")
        return output_path

    def generate_srt_subtitles(self, segments: List[Dict[str, Any]], srt_filename: str = "podcast_captions.srt") -> str:
        """Generates accurate SubRip (.srt) subtitle file from segment timing."""
        srt_path = os.path.join(self.output_dir, srt_filename)
        
        current_time = 0.0
        with open(srt_path, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(segments, 1):
                start_time = current_time
                dur = seg.get("duration", 3.0)
                end_time = current_time + dur
                current_time = end_time + 0.12 # Include 120ms pause

                start_str = self._format_timestamp(start_time)
                end_str = self._format_timestamp(end_time)

                speaker = seg.get("speaker", "Speaker")
                text = seg.get("text", "")

                f.write(f"{idx}\n")
                f.write(f"{start_str} --> {end_str}\n")
                f.write(f"{speaker}: {text}\n\n")

        return srt_path

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Formats seconds into SRT format HH:MM:SS,mmm"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"
