import os
import re
import sys
import time
import shutil
import asyncio
import subprocess
from typing import Optional, Dict, Any

class VoiceCloneEngine:
    """
    OpenVoice v2 Neural Voice Cloning Engine for PodcastAI.
    Converts speech dialogue turns for Student / Monika / Host
    into the user's authentic cloned voice based on their recorded sample.
    """

    def __init__(self, clone_dir: str = "web/static/voice_clone", output_dir: str = "outputs", device: str = "cpu"):
        self.clone_dir = clone_dir
        self.output_dir = output_dir
        self.device = device
        self.reference_wav = os.path.join(self.clone_dir, "my_voice.wav")
        self.reference_mp3 = os.path.join(self.clone_dir, "my_voice.mp3")
        
        os.makedirs(self.clone_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

        self.converter = None
        self.cached_tgt_se = None
        self.cached_ref_mtime = 0
        self.cached_src_se = {}
        self._init_neural_converter()

    def _init_neural_converter(self):
        """Loads the OpenVoice neural tone color converter model into memory."""
        try:
            import openvoice_cli
            from openvoice_cli.api import ToneColorConverter
            
            base_dir = os.path.dirname(openvoice_cli.__file__)
            ckpt_converter = os.path.join(base_dir, 'checkpoints', 'converter')
            config_path = os.path.join(ckpt_converter, 'config.json')
            checkpoint_path = os.path.join(ckpt_converter, 'checkpoint.pth')

            if os.path.exists(config_path) and os.path.exists(checkpoint_path):
                self.converter = ToneColorConverter(config_path, device=self.device)
                self.converter.load_ckpt(checkpoint_path)
                print("[VoiceCloneEngine] OpenVoice v2 Neural Converter loaded successfully on", self.device)
                self._update_target_se()
        except Exception as e:
            print(f"[VoiceCloneEngine] Notice: Neural converter init: {e}")

    def _update_target_se(self):
        """Extracts and caches the user's voice embedding from my_voice.wav."""
        ref_path = self.get_reference_path()
        if not ref_path or not self.converter:
            self.cached_tgt_se = None
            return

        try:
            mtime = os.path.getmtime(ref_path)
            if self.cached_tgt_se is None or mtime != self.cached_ref_mtime:
                # Normalize reference to 16kHz mono wav if needed
                norm_ref = os.path.join(self.clone_dir, "my_voice_16k.wav")
                cmd = ["ffmpeg", "-y", "-i", ref_path, "-ar", "16000", "-ac", "1", norm_ref]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                
                self.cached_tgt_se = self.converter.extract_se([norm_ref])
                self.cached_ref_mtime = mtime
                print("[VoiceCloneEngine] Extracted and cached user target speaker embedding!")
        except Exception as e:
            print(f"[VoiceCloneEngine] Failed to extract target SE: {e}")
            self.cached_tgt_se = None

    def has_voice_clone(self) -> bool:
        """Returns True if a valid user voice recording exists."""
        if os.path.exists(self.reference_wav) and os.path.getsize(self.reference_wav) > 1000:
            return True
        if os.path.exists(self.reference_mp3) and os.path.getsize(self.reference_mp3) > 1000:
            return True
        return False

    def get_reference_path(self) -> Optional[str]:
        """Returns absolute path to user's reference voice sample if available."""
        if os.path.exists(self.reference_wav) and os.path.getsize(self.reference_wav) > 1000:
            return os.path.abspath(self.reference_wav)
        if os.path.exists(self.reference_mp3) and os.path.getsize(self.reference_mp3) > 1000:
            return os.path.abspath(self.reference_mp3)
        return None

    def save_reference_audio(self, source_file_path: str) -> bool:
        """Converts incoming user recording to standard 16kHz mono WAV and updates embedding cache."""
        try:
            target_wav = self.reference_wav
            cmd = [
                "ffmpeg", "-y", "-i", source_file_path,
                "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
                target_wav
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self._update_target_se()
            return True
        except Exception as e:
            print(f"[VoiceCloneEngine] Error saving reference audio: {e}")
            try:
                shutil.copy(source_file_path, self.reference_wav)
                self._update_target_se()
                return True
            except Exception as copy_err:
                print(f"[VoiceCloneEngine] Copy fallback failed: {copy_err}")
                return False

    def delete_voice_clone(self) -> bool:
        """Deletes user's cloned voice reference file to reset to AI default."""
        try:
            if os.path.exists(self.reference_wav):
                os.remove(self.reference_wav)
            if os.path.exists(self.reference_mp3):
                os.remove(self.reference_mp3)
            norm_ref = os.path.join(self.clone_dir, "my_voice_16k.wav")
            if os.path.exists(norm_ref):
                os.remove(norm_ref)
            self.cached_tgt_se = None
            return True
        except Exception as e:
            print(f"[VoiceCloneEngine] Failed to delete voice clone: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Returns voice cloning status and details for UI badges."""
        has_clone = self.has_voice_clone()
        ref_path = self.get_reference_path()
        duration = 0.0
        if has_clone and ref_path:
            try:
                cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", ref_path]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                duration = round(float(res.stdout.strip()), 1)
            except Exception:
                duration = 5.0

        return {
            "has_cloned_voice": has_clone,
            "status_text": "🟢 Cloned Voice Active (My Voice)" if has_clone else "⚪ AI Voice Default (Edge-TTS)",
            "voice_url": "/static/voice_clone/my_voice.wav" if has_clone else None,
            "duration": duration,
            "openvoice_neural_engine": self.converter is not None
        }

    async def synthesize_cloned_segment(
        self,
        text: str,
        output_filename: str,
        base_voice: str = "en-US-EmmaNeural",
        emotion: str = "neutral"
    ) -> Dict[str, Any]:
        """
        Synthesizes speech and clones user's voice using OpenVoice neural tone conversion.
        """
        out_path = os.path.join(self.output_dir, output_filename)
        temp_src_mp3 = os.path.join(self.output_dir, f"temp_src_{output_filename}")
        temp_src_wav = os.path.join(self.output_dir, f"temp_src_{output_filename}.wav")
        temp_cloned_wav = os.path.join(self.output_dir, f"temp_cloned_{output_filename}.wav")

        # 1. Generate clean base expressive speech with natural human pacing
        import edge_tts
        from core.tts_engine import EMOTION_PROSODY
        prosody = EMOTION_PROSODY.get(emotion.lower(), {"rate": "+0%", "pitch": "+0Hz"})
        
        communicate = edge_tts.Communicate(
            text=text,
            voice=base_voice,
            rate=prosody["rate"],
            pitch=prosody["pitch"]
        )
        
        with open(temp_src_mp3, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

        # Convert src to 16kHz mono WAV for OpenVoice
        cmd_wav = ["ffmpeg", "-y", "-i", temp_src_mp3, "-ar", "16000", "-ac", "1", temp_src_wav]
        subprocess.run(cmd_wav, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        cloned_success = False

        # 2. Neural Voice Cloning via OpenVoice
        if self.converter is not None:
            if self.cached_tgt_se is None:
                self._update_target_se()

            if self.cached_tgt_se is not None:
                try:
                    if base_voice not in self.cached_src_se:
                        self.cached_src_se[base_voice] = self.converter.extract_se([temp_src_wav])
                    src_se = self.cached_src_se[base_voice]
                    self.converter.convert(
                        audio_src_path=temp_src_wav,
                        src_se=src_se,
                        tgt_se=self.cached_tgt_se,
                        output_path=temp_cloned_wav
                    )
                    if os.path.exists(temp_cloned_wav) and os.path.getsize(temp_cloned_wav) > 1000:
                        shutil.copy(temp_cloned_wav, out_path)
                        cloned_success = True
                except Exception as e:
                    print(f"[VoiceCloneEngine] Neural clone turn failed, falling back: {e}")

        if not cloned_success:
            cmd_fallback = [
                "ffmpeg", "-y", "-i", temp_src_mp3,
                "-af", "highpass=f=60,equalizer=f=2500:t=q:w=1.0:g=1.2,volume=1.1",
                "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "192k",
                out_path
            ]
            try:
                subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except Exception:
                shutil.copy(temp_src_mp3, out_path)

        # Cleanup temporary files
        for tmp_file in [temp_src_mp3, temp_src_wav, temp_cloned_wav]:
            if os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass

        # Calculate duration
        duration = 3.0
        try:
            cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", out_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            duration = float(res.stdout.strip())
        except Exception:
            pass

        return {
            "audio_path": out_path,
            "duration": duration,
            "subtitles": ""
        }
