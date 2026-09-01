import os
import shutil
import json
import time
import sys
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.rag_processor import DocumentProcessor
from core.script_generator import ScriptGenerator
from core.tts_engine import TTSEngine
from core.audio_mixer import AudioMixer
from core.local_video_renderer import LocalVideoRenderer
from core.evaluation_metrics import EvaluationMetrics

app = FastAPI(
    title="AI Podcast & Educational Transcript Platform",
    description="Automated Podcast Generation and Educational MS Teams / Class Transcript Audio Synthesizer",
    version="2.0.0"
)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
UPLOAD_DIR = os.path.join(OUTPUT_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "web", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "web", "templates")
HISTORY_FILE = os.path.join(OUTPUT_DIR, "history.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount Static Files & Templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Instantiate Core Engines
tts_engine = TTSEngine(output_dir=OUTPUT_DIR)
audio_mixer = AudioMixer(output_dir=OUTPUT_DIR)
video_renderer = LocalVideoRenderer(output_dir=OUTPUT_DIR, base_dir=BASE_DIR)
script_gen = ScriptGenerator()

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """Renders the main Podcast & Transcript Studio web interface."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/history")
async def get_history():
    """Returns past podcast/transcript generation history."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return JSONResponse(json.load(f))
        except Exception:
            pass
    return JSONResponse([])

@app.delete("/api/history/{item_id}")
async def delete_history_item(item_id: str):
    """Deletes a specific entry and its files from history."""
    if not os.path.exists(HISTORY_FILE):
        raise HTTPException(status_code=404, detail="History not found")

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)

        updated_history = []
        deleted_entry = None

        for entry in history:
            if entry.get("id") == item_id:
                deleted_entry = entry
            else:
                updated_history.append(entry)

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(updated_history, f, indent=2)

        if deleted_entry:
            for key in ["audio_url", "video_url", "srt_url", "script_url"]:
                url = deleted_entry.get(key, "")
                if url and url.startswith("/outputs/"):
                    fname = os.path.basename(url)
                    fpath = os.path.join(OUTPUT_DIR, fname)
                    if os.path.exists(fpath):
                        try:
                            os.remove(fpath)
                        except Exception:
                            pass

        return JSONResponse({"status": "deleted", "id": item_id})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voice-clone/status")
async def get_voice_clone_status():
    """Returns the current status of user's cloned voice."""
    status = tts_engine.voice_clone_engine.get_status()
    return JSONResponse(status)

@app.post("/api/voice-clone/upload")
async def upload_voice_clone_sample(voice_file: UploadFile = File(...)):
    """Uploads or saves a microphone-recorded voice sample for cloning."""
    try:
        temp_sample_path = os.path.join(UPLOAD_DIR, f"temp_voice_{int(time.time())}_{voice_file.filename}")
        with open(temp_sample_path, "wb") as f:
            content = await voice_file.read()
            f.write(content)

        success = tts_engine.voice_clone_engine.save_reference_audio(temp_sample_path)
        if os.path.exists(temp_sample_path):
            try:
                os.remove(temp_sample_path)
            except Exception:
                pass

        if not success:
            raise HTTPException(status_code=500, detail="Failed to convert/save reference voice.")

        status = tts_engine.voice_clone_engine.get_status()
        return JSONResponse({
            "status": "success",
            "message": "Voice sample successfully cloned and activated!",
            **status
        })
    except Exception as e:
        print(f"[VoiceClone API] Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice-clone/delete")
async def delete_voice_clone():
    """Resets the voice clone back to default AI voice."""
    try:
        tts_engine.voice_clone_engine.delete_voice_clone()
        status = tts_engine.voice_clone_engine.get_status()
        return JSONResponse({
            "status": "success",
            "message": "Voice clone deleted. Reverted to AI voice.",
            **status
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-podcast")
async def generate_podcast(
    topic: Optional[str] = Form(None),
    duration: float = Form(3.0),
    style: str = Form("Informative & Engaging"),
    host_voice: str = Form("en-US-EmmaNeural"),
    guest_voice: str = Form("en-US-ChristopherNeural"),
    api_key: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None)
):
    """
    End-to-End Endpoint supporting 2 Modes:
    1. General Topic Podcast Mode
    2. Educational Lecture / Meeting Transcript Mode
    """
    try:
        if api_key and api_key.strip().lower() in ["string", "none", "null", ""]:
            api_key = None

        clean_topic = topic.strip() if topic and topic.strip() and topic.strip().lower() != "string" else ""
        parsed_transcript_turns = None
        unique_speakers = []
        is_transcript_mode = False

        if pdf_file and pdf_file.filename and pdf_file.filename.strip():
            temp_file_path = os.path.join(OUTPUT_DIR, f"temp_{pdf_file.filename}")
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(pdf_file.file, buffer)
            
            # Parse MS Teams / Zoom / Class Transcript
            parsed_transcript_turns, unique_speakers = DocumentProcessor.parse_meeting_transcript(temp_file_path)
            is_transcript_mode = True

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

            if not clean_topic:
                clean_topic = os.path.splitext(pdf_file.filename)[0].replace("_", " ")

        script_gen = ScriptGenerator(api_key=api_key)
        dialogue = script_gen.generate_script(
            topic=clean_topic or "Podcast Session",
            parsed_transcript=parsed_transcript_turns,
            duration_minutes=duration,
            podcast_style=style,
            host_name="Monika (Host)",
            guest_name="Dr. Alex (Guest)"
        )

        # Synthesize multi-speaker audio with dynamic N-speaker voices
        segments = await tts_engine.synthesize_podcast_dialogue(
            dialogue=dialogue,
            host_voice=host_voice,
            guest_voice=guest_voice
        )

        run_id = f"podcast_{int(time.time())}"
        audio_filename = f"{run_id}_audio.mp3"
        video_filename = f"{run_id}_video.mp4"
        srt_filename = f"{run_id}_captions.srt"
        script_filename = f"{run_id}_script.json"

        master_audio_path = audio_mixer.concatenate_segments(segments, master_filename=audio_filename)
        srt_path = audio_mixer.generate_srt_subtitles(segments, srt_filename=srt_filename)

        # Save JSON script file for export and GPU Studio compositing
        script_file_path = os.path.join(OUTPUT_DIR, script_filename)
        with open(script_file_path, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2)

        final_video_path = video_renderer.render_podcast_video(
            segments=segments,
            master_audio_path=master_audio_path,
            output_filename=video_filename,
            podcast_title=clean_topic or "Podcast Session",
            host_voice=host_voice,
            guest_voice=guest_voice
        )

        metrics = EvaluationMetrics.analyze_script_metrics(dialogue)

        result_payload = {
            "id": run_id,
            "topic": clean_topic or ("Educational Class Transcript" if is_transcript_mode else "General Podcast Topic"),
            "title": clean_topic or ("Educational Class Transcript" if is_transcript_mode else "General Podcast Topic"),
            "mode": "transcript" if is_transcript_mode else "podcast",
            "speakers": unique_speakers if is_transcript_mode else ["Monika (Host)", "Dr. Alex (Guest)"],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "dialogue": dialogue,
            "audio_url": f"/outputs/{audio_filename}",
            "video_url": f"/outputs/{video_filename}",
            "srt_url": f"/outputs/{srt_filename}",
            "script_url": f"/outputs/{script_filename}",
            "metrics": metrics
        }

        save_to_history(result_payload)

        return JSONResponse({
            "status": "success",
            **result_payload
        })

    except Exception as e:
        print(f"[API Error] Failed to generate: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pdf-chapters/extract")
async def extract_pdf_chapters(pdf_file: UploadFile = File(...)):
    """Uploads a textbook/course PDF and extracts chapter-wise sections."""
    try:
        temp_pdf_path = os.path.join(UPLOAD_DIR, f"textbook_{int(time.time())}_{pdf_file.filename}")
        with open(temp_pdf_path, "wb") as f:
            content = await pdf_file.read()
            f.write(content)

        chapters = DocumentProcessor.extract_chapters_from_pdf(temp_pdf_path)
        return JSONResponse({
            "status": "success",
            "filename": pdf_file.filename,
            "total_chapters": len(chapters),
            "chapters": chapters
        })
    except Exception as e:
        print(f"[API Error] PDF Chapter extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pdf-chapters/generate-chapter-audio")
async def generate_chapter_audio(
    chapter_title: str = Form(...),
    chapter_content: str = Form(...),
    host_voice: str = Form("en-US-EmmaNeural"),
    guest_voice: str = Form("en-US-ChristopherNeural")
):
    """Generates an interactive student-professor audio lesson for a specific textbook chapter."""
    try:
        dialogue = script_gen.generate_chapter_script(
            chapter_title=chapter_title,
            chapter_content=chapter_content,
            host_name="Monika (Host)",
            guest_name="Dr. Alex (Expert)"
        )

        segments = await tts_engine.synthesize_podcast_dialogue(
            dialogue=dialogue,
            host_voice=host_voice,
            guest_voice=guest_voice
        )

        run_id = f"chapter_{int(time.time())}"
        audio_filename = f"{run_id}_audio.mp3"
        video_filename = f"{run_id}_video.mp4"
        srt_filename = f"{run_id}_captions.srt"

        master_audio_path = audio_mixer.concatenate_segments(segments, master_filename=audio_filename)
        audio_mixer.generate_srt_subtitles(segments, srt_filename=srt_filename)

        video_path = video_renderer.render_podcast_video(
            segments=segments,
            master_audio_path=master_audio_path,
            output_filename=video_filename,
            podcast_title=chapter_title,
            host_voice=host_voice,
            guest_voice=guest_voice
        )

        metrics = EvaluationMetrics.analyze_script_metrics(dialogue)

        save_to_history({
            "id": run_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mode": "pdf",
            "title": f"Chapter Learning: {chapter_title}",
            "audio_url": f"/outputs/{audio_filename}",
            "video_url": f"/outputs/{video_filename}",
            "turns_count": len(dialogue),
            "metrics": metrics
        })

        return JSONResponse({
            "status": "success",
            "chapter_title": chapter_title,
            "audio_url": f"/outputs/{audio_filename}",
            "video_url": f"/outputs/{video_filename}",
            "dialogue": dialogue,
            "segments": segments,
            "metrics": metrics
        })
    except Exception as e:
        print(f"[API Error] Chapter audio generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pdf-chapters/ask-question")
async def ask_professor_question(
    chapter_title: str = Form(...),
    chapter_content: str = Form(...),
    question: str = Form(...),
    guest_voice: str = Form("en-US-ChristopherNeural")
):
    """Answers a live doubt question in Dr. Alex's voice."""
    try:
        answer_text = script_gen.answer_student_question(
            chapter_title=chapter_title,
            chapter_content=chapter_content,
            question=question,
            expert_name="Dr. Alex (Expert)"
        )

        audio_filename = f"qa_ans_{int(time.time())}.mp3"
        audio_path = os.path.join(OUTPUT_DIR, audio_filename)

        await tts_engine.generate_speech_segment(
            text=answer_text,
            voice=guest_voice,
            output_filename=audio_filename,
            emotion="explaining"
        )

        return JSONResponse({
            "status": "success",
            "question": question,
            "answer_text": answer_text,
            "audio_url": f"/outputs/{audio_filename}"
        })
    except Exception as e:
        print(f"[API Error] Ask question failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def save_to_history(entry: dict):
    """Saves entry to persistent JSON history file."""
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    history.insert(0, entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[:30], f, indent=2)

if __name__ == "__main__":
    import uvicorn
    
    target_port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        target_port = int(sys.argv[1])

    ports_to_try = [target_port, 8080, 8050, 5000]
    started = False

    for p in ports_to_try:
        try:
            print(f"[PodcastAI] Attempting to start server on http://127.0.0.1:{p} ...")
            uvicorn.run("app:app", host="127.0.0.1", port=p, reload=True)
            started = True
            break
        except Exception as err:
            print(f"[PodcastAI] Port {p} unavailable ({err}), trying next port...")

    if not started:
        print("ERROR: Could not bind to any port. Please stop conflicting processes.")
