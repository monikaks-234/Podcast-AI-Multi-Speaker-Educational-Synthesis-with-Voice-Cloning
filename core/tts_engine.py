import os
import re
import asyncio
import edge_tts
from typing import List, Dict, Any, Tuple
from core.voice_clone_engine import VoiceCloneEngine

DEFAULT_VOICES = {
    "Host_Male": "en-US-ChristopherNeural",
    "Host_Female": "en-US-EmmaNeural",
    "Guest_Male": "en-US-ChristopherNeural",
    "Guest_Female": "en-US-EmmaNeural",
}

MALE_VOICE_POOL = [
    "en-US-ChristopherNeural",
    "en-US-GuyNeural",
    "en-GB-RyanNeural",
    "en-IN-PrabhatNeural"
]

FEMALE_VOICE_POOL = [
    "en-US-EmmaNeural",
    "en-US-AvaNeural",
    "en-GB-SoniaNeural",
    "en-IN-NeerjaNeural"
]

FEMALE_NAME_KEYWORDS = ["monika", "dr", "shinu", "sandra", "emma", "ava", "neerja", "sonia", "mary", "sarah", "priya", "lata", "sumalatha", "ann", "ma'am", "madam", "mrs", "ms"]

EMOTION_PROSODY = {
    "enthusiastic": {"rate": "+4%", "pitch": "+4Hz"},
    "curious": {"rate": "+0%", "pitch": "+6Hz"},
    "analytical": {"rate": "-2%", "pitch": "-1Hz"},
    "thoughtful": {"rate": "-4%", "pitch": "-3Hz"},
    "explaining": {"rate": "+0%", "pitch": "+2Hz"},
    "neutral": {"rate": "+0%", "pitch": "+0Hz"}
}

class TTSEngine:
    """
    Multi-speaker expressive audio synthesis using Edge-TTS and OpenVoice Neural Voice Cloning.
    Uses user's cloned voice for Host / Student / Monika when a voice sample is registered.
    Uses natural human pacing, pitch modulation, and studio-grade audio mastering.
    """

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.voice_clone_engine = VoiceCloneEngine(output_dir=self.output_dir)

    def _is_female_speaker(self, name: str) -> bool:
        """Helper to infer female gender from speaker name keywords."""
        name_lower = name.lower()
        for kw in FEMALE_NAME_KEYWORDS:
            if kw in name_lower:
                return True
        return False

    async def generate_speech_segment(
        self,
        text: str,
        voice: str = "en-US-ChristopherNeural",
        output_filename: str = "segment.mp3",
        emotion: str = "neutral"
    ) -> Dict[str, Any]:
        """Generates audio for a single dialogue line with natural expressive prosody and studio EQ."""
        prosody = EMOTION_PROSODY.get(emotion.lower(), EMOTION_PROSODY["neutral"])
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=prosody["rate"],
            pitch=prosody["pitch"]
        )

        out_path = os.path.join(self.output_dir, output_filename)
        submaker = edge_tts.SubMaker()
        
        with open(out_path, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        duration = self._get_audio_duration(out_path)
        return {
            "audio_path": out_path,
            "duration": duration,
            "subtitles": submaker.get_srt() if hasattr(submaker, 'get_srt') else ""
        }

    async def synthesize_podcast_dialogue(
        self,
        dialogue: List[Dict[str, str]],
        host_voice: str = "en-US-EmmaNeural",
        guest_voice: str = "en-US-ChristopherNeural"
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously synthesizes multi-speaker dialogue.
        Maps Host (Monika/Student) to user's Cloned Voice (or host_voice)
        and Guest (Simha Sir/Professor/Dr. Alex) to user-selected guest_voice (Male AI).
        """
        unique_speakers = []
        for turn in dialogue:
            spk = turn.get("speaker", "Presenter").strip()
            if spk and spk not in unique_speakers:
                unique_speakers.append(spk)

        speaker_voice_map = {}
        speaker_is_clone_map = {}
        has_cloned_voice = self.voice_clone_engine.has_voice_clone()

        for idx, spk in enumerate(unique_speakers):
            spk_lower = spk.lower()
            is_host = ("host" in spk_lower or "monika" in spk_lower or "student" in spk_lower) and not ("alex" in spk_lower or "guest" in spk_lower or "prof" in spk_lower)
            if idx == 0 and not ("alex" in spk_lower or "guest" in spk_lower or "prof" in spk_lower):
                is_host = True

            if is_host:
                speaker_voice_map[spk] = host_voice  # Base female voice
                speaker_is_clone_map[spk] = has_cloned_voice
            elif "guest" in spk_lower or "prof" in spk_lower or "simha" in spk_lower or "dr" in spk_lower or "alex" in spk_lower or idx == 1:
                speaker_voice_map[spk] = guest_voice # Male guest AI voice
                speaker_is_clone_map[spk] = False
            elif self._is_female_speaker(spk):
                speaker_voice_map[spk] = FEMALE_VOICE_POOL[idx % len(FEMALE_VOICE_POOL)]
                speaker_is_clone_map[spk] = False
            else:
                speaker_voice_map[spk] = MALE_VOICE_POOL[idx % len(MALE_VOICE_POOL)]
                speaker_is_clone_map[spk] = False

        tasks = []
        for idx, turn in enumerate(dialogue):
            speaker = turn.get("speaker", "Presenter").strip()
            text = turn.get("text", "")
            emotion = turn.get("emotion", "neutral")
            
            voice = speaker_voice_map.get(speaker, host_voice)
            is_cloned = speaker_is_clone_map.get(speaker, False)
            safe_spk_name = "".join(c for c in speaker if c.isalnum() or c == '_').rstrip()
            out_name = f"segment_{idx:03d}_{safe_spk_name}.mp3"
            
            if is_cloned:
                tasks.append(self.voice_clone_engine.synthesize_cloned_segment(text, out_name, base_voice=voice, emotion=emotion))
            else:
                tasks.append(self.generate_speech_segment(text, voice, out_name, emotion))
            
        results = await asyncio.gather(*tasks)

        segments = []
        for idx, (turn, result) in enumerate(zip(dialogue, results)):
            speaker = turn.get("speaker", "Presenter").strip()
            text = turn.get("text", "")
            emotion = turn.get("emotion", "neutral")
            segments.append({
                "index": idx,
                "speaker": speaker,
                "text": text,
                "emotion": emotion,
                "audio_path": result["audio_path"],
                "duration": result["duration"]
            })
            
        return segments

    def synthesize_podcast_dialogue_sync(
        self,
        dialogue: List[Dict[str, str]],
        host_voice: str = "en-US-EmmaNeural",
        guest_voice: str = "en-US-ChristopherNeural"
    ) -> List[Dict[str, Any]]:
        """Synchronous wrapper for non-async scripts."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    lambda: asyncio.run(self.synthesize_podcast_dialogue(dialogue, host_voice, guest_voice))
                ).result()
        else:
            return loop.run_until_complete(
                self.synthesize_podcast_dialogue(dialogue, host_voice, guest_voice)
            )

    def _get_audio_duration(self, audio_path: str) -> float:
        """Helper to get audio duration in seconds."""
        try:
            import subprocess
            cmd = [
                "ffprobe", "-v", "error", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                return float(res.stdout.strip())
        except Exception:
            pass
        
        if os.path.exists(audio_path):
            size = os.path.getsize(audio_path)
            return round(size / 16000.0, 2)
        return 3.0
