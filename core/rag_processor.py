import os
import re
from typing import Dict, Any, List, Tuple
from pypdf import PdfReader

class DocumentProcessor:
    """
    Extracts and cleans MS Teams / Zoom educational class transcripts across ALL layout formats:
    Format 1: "RACE Support 22:19", "omnaveen ks 22:41" (Teams Web & App Export with Timestamp Headers)
    Format 2: "Anirban Dasgupta \n 0 minutes 4 seconds" (Teams Meeting Recording Transcript)
    Format 3: "0:04 Speaker Name \n Spoken text" (Zoom / VTT / SRT Format)

    Automatically filters header metadata, extracts dynamic speaker names, and produces clean multi-speaker dialogue turns.
    """

    @staticmethod
    def extract_text_from_pdf(pdf_path: str, max_pages: int = 200) -> str:
        """Extracts full text content from a PDF file."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        reader = PdfReader(pdf_path)
        extracted_text = []
        
        num_pages = min(len(reader.pages), max_pages)
        for idx in range(num_pages):
            page_text = reader.pages[idx].extract_text()
            if page_text:
                extracted_text.append(page_text.strip())
                
        full_text = "\n\n".join(extracted_text)
        return full_text

    @classmethod
    def parse_meeting_transcript(cls, file_path: str) -> Tuple[List[Dict[str, str]], List[str]]:
        """
        Universal Parser for MS Teams / Zoom meeting transcripts (PDF, TXT, VTT, SRT).
        Returns:
            dialogue_turns: Cleaned list of {"speaker": speaker_name, "text": clean_spoken_text}
            unique_speakers: List of all unique speaker names detected
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            raw_text = cls.extract_text_from_pdf(file_path)
        elif ext in [".txt", ".md", ".vtt", ".srt"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read().strip()
        else:
            raise ValueError(f"Unsupported transcript format: {ext}")

        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        
        # 1. Filter out Document Header Metadata (e.g. "Meeting Recording", "August 1, 2026", "1h 37m 32s", "started transcription")
        metadata_skip_patterns = [
            r'started transcription', r'Meeting Recording', r'^\d{1,2}h\s*\d{1,2}m',
            r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}',
            r'^\d{1,2}:\d{2}\s*(AM|PM)'
        ]

        def is_metadata_header(line_str):
            for pat in metadata_skip_patterns:
                if re.search(pat, line_str, re.IGNORECASE):
                    return True
            return False

        clean_lines = [l for l in lines if not is_metadata_header(l)]

        dialogue_turns = []
        unique_speakers = []
        
        current_speaker = None
        current_text_lines = []

        # Regex Format A: "RACE Support 22:19", "OK omnaveen ks 22:41", "RS RACE Support 23:20"
        format_a_regex = r'^(?:[A-Z0-9]{2}\s+)?([A-Za-z0-9_.\-\s]+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)$'
        
        # Regex Format B: Standard Speaker Heading e.g. "Anirban Dasgupta", "Dr. Shinu Abhi"
        format_b_regex = r'^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)?\s*[A-Z][a-z0-9A-Z_.-]+(\s+[A-Z][a-z0-9A-Z_.-]+)*$'

        # Skip noise patterns
        skip_patterns = [
            r'^\d+\s*(minutes|minute|seconds|second|hours|hour)', # '0 minutes 4 seconds'
            r'^\d+:\d+(:\d+)?$',                                    # '0:04', '1:27:18'
            r'^[A-Z]{2}$',                                         # 'AD', 'SS', 'AS', 'PR'
            r'^(Sound music\.?|Laughter|Applause|Noise)$'           # Non-speech sound cues
        ]

        def is_skip_line(line_str):
            for pat in skip_patterns:
                if re.search(pat, line_str, re.IGNORECASE):
                    return True
            return False

        def clean_line_text(line_str, active_speaker):
            cleaned = line_str
            cleaned = re.sub(r'[A-Z][a-z]+(\s+[A-Z][a-z]+)*\s+\d+\s*(minutes|minute|seconds|second|hours|hour)(\s*\d+:\d+)?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'^\d+\s*(minutes|minute|seconds|second|hours|hour)(\s*\d+:\d+)?', '', cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', '', cleaned)
            
            if active_speaker and cleaned.startswith(active_speaker):
                cleaned = cleaned[len(active_speaker):].strip()
                
            return cleaned.strip()

        for line in clean_lines:
            if is_skip_line(line):
                continue

            # Check Format A (Name + Timestamp Header e.g. "omnaveen ks 22:41")
            match_a = re.match(format_a_regex, line)
            
            # Check Format B (Pure Speaker Name Header)
            words = line.split()
            is_match_b = (len(words) <= 5 and re.match(format_b_regex, line) and 
                          not (line.endswith('?') or line.endswith('!') or (line.endswith('.') and not line.startswith(('Dr.', 'Prof.', 'Mr.', 'Ms.')))))

            if match_a:
                spk_name = match_a.group(1).strip()
                if current_speaker and current_text_lines:
                    full_text_str = " ".join(current_text_lines).strip()
                    if len(full_text_str) >= 2:
                        dialogue_turns.append({"speaker": current_speaker, "text": full_text_str})
                    current_text_lines = []

                current_speaker = spk_name
                if current_speaker not in unique_speakers:
                    unique_speakers.append(current_speaker)

            elif is_match_b:
                spk_name = line.strip()
                if current_speaker and current_text_lines:
                    full_text_str = " ".join(current_text_lines).strip()
                    if len(full_text_str) >= 2:
                        dialogue_turns.append({"speaker": current_speaker, "text": full_text_str})
                    current_text_lines = []

                current_speaker = spk_name
                if current_speaker not in unique_speakers:
                    unique_speakers.append(current_speaker)
            else:
                if current_speaker:
                    cleaned_str = clean_line_text(line, current_speaker)
                    if cleaned_str and not is_skip_line(cleaned_str):
                        current_text_lines.append(cleaned_str)

        # Flush final turn
        if current_speaker and current_text_lines:
            full_text_str = " ".join(current_text_lines).strip()
            if len(full_text_str) >= 2:
                dialogue_turns.append({"speaker": current_speaker, "text": full_text_str})

        # Fallback if no speaker headers detected
        if not dialogue_turns and clean_lines:
            cleaned_body = " ".join([clean_line_text(l, "") for l in clean_lines if not is_skip_line(l)])
            if cleaned_body:
                dialogue_turns = [{
                    "speaker": "Speaker 1",
                    "text": cleaned_body
                }]
                unique_speakers = ["Speaker 1"]

        return dialogue_turns, unique_speakers

    @classmethod
    def get_grounded_context(cls, file_path: str) -> str:
        """Determines file type and extracts raw context text."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return cls.extract_text_from_pdf(file_path)
        elif ext in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        else:
            raise ValueError(f"Unsupported document format: {ext}")

    @classmethod
    def extract_chapters_from_pdf(cls, file_path: str) -> List[Dict[str, Any]]:
        """
        Extracts chapter-wise sections from a textbook/course PDF (School to Degree level).
        Accurately parses 'Chapter 1: Preliminaries', handles multi-line titles,
        eliminates running headers & mathematical false positives (e.g. 'Unit vector normal').
        """
        raw_text = cls.get_grounded_context(file_path)
        if not raw_text or len(raw_text.strip()) < 50:
            raise ValueError("The uploaded PDF contains insufficient text content.")

        # Clean PDF ligature characters (fi, fl, ff, ffi, ffl) and quotes
        raw_text = raw_text.replace('\ufb01', 'fi').replace('\ufb02', 'fl').replace('\ufb00', 'ff').replace('\ufb03', 'ffi').replace('\ufb04', 'ffl')
        raw_text = raw_text.replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('ﬀ', 'ff').replace('ﬃ', 'ffi').replace('ﬄ', 'ffl')
        raw_text = raw_text.replace('’', "'").replace('“', '"').replace('”', '"')

        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        
        # Precise chapter heading regex (supports Chapter, Module, Unit, Lesson followed by number or strict Roman numeral)
        chapter_num_pattern = re.compile(r'^(Chapter|Module|Unit|Lesson)\s+(\d+|[IVXLCDM]+(?=\s*[:\.\-\s]|$))[:\s\-\.]*(.*)$', re.IGNORECASE)
        
        # Blacklist of false positive technical terms starting with Unit / Section
        false_unit_words = ["vector", "circle", "step", "interval", "cost", "matrix", "norm", "test", "sample", "hyperplane", "distance", "sphere", "cube"]

        raw_chapters = []
        current_num = None
        current_title = ""
        current_lines = []

        idx = 0
        while idx < len(lines):
            line = lines[idx]
            
            # Skip running headers / page numbers (e.g. "2 CHAPTER 1. PRELIMINARIES")
            if re.search(r'^\d+\s+(chapter|module|unit)', line, re.I) or (re.search(r'(chapter|module|unit).*\d+$', line, re.I) and len(line.split()) <= 6):
                if re.match(r'^\d+\s+[A-Z\s\.\:\-]+$', line):
                    idx += 1
                    continue

            match = chapter_num_pattern.match(line)
            
            # Validate chapter candidate
            is_valid_chapter = False
            if match and len(line) < 80:
                chap_type = match.group(1).capitalize()
                chap_num_raw = match.group(2).strip()
                suffix = match.group(3).strip()
                
                suffix_first_word = suffix.split()[0].lower() if suffix else ""
                if chap_type == "Unit" and (suffix_first_word in false_unit_words or (chap_num_raw.lower() in ['v', 'i', 'x'] and suffix_first_word.startswith('ector'))):
                    is_valid_chapter = False
                elif re.search(r'\b(in|of|from|see|to|by|per|with|for)\s+(chapter|module|unit)\b', line, re.I):
                    is_valid_chapter = False
                else:
                    is_valid_chapter = True

            if is_valid_chapter:
                chap_type = match.group(1).capitalize()
                chap_num_raw = match.group(2).strip()
                suffix = match.group(3).strip()

                # Clean suffix punctuation
                suffix = re.sub(r'^[–—:\-\.\s]+', '', suffix).strip()
                
                # Multi-line title assembly: collect up to 2 title continuation lines before subheadings/sections begin
                title_parts = []
                if suffix:
                    title_parts.append(suffix)
                
                lookahead = idx + 1
                while lookahead < len(lines) and len(title_parts) < 2:
                    next_l = lines[lookahead]
                    if re.match(r'^\d+\.\d+', next_l) or chapter_num_pattern.match(next_l) or len(next_l) > 60:
                        break
                    if not re.match(r'^[a-z]', next_l) or len(title_parts) > 0:
                        title_parts.append(next_l)
                        idx = lookahead
                        lookahead += 1
                    else:
                        break

                full_suffix = " ".join(title_parts).strip()
                full_title = f"{chap_type} {chap_num_raw}"
                if full_suffix:
                    full_title += f": {full_suffix}"

                # Save previous chapter if it had valid content
                if current_num is not None and current_lines:
                    chapter_text = "\n".join(current_lines).strip()
                    if len(chapter_text) > 30:
                        raw_chapters.append({
                            "chapter_id": len(raw_chapters) + 1,
                            "title": current_title,
                            "content": chapter_text
                        })

                # Start new chapter
                current_num = chap_num_raw
                current_title = full_title
                current_lines = []
            else:
                if current_num is not None:
                    current_lines.append(line)

            idx += 1

        # Save final chapter
        if current_num is not None and current_lines:
            chapter_text = "\n".join(current_lines).strip()
            if len(chapter_text) > 30:
                raw_chapters.append({
                    "chapter_id": len(raw_chapters) + 1,
                    "title": current_title,
                    "content": chapter_text
                })

        # Fallback if no explicit "Chapter X" headers were matched
        if not raw_chapters:
            full_text = "\n".join(lines)
            chunk_size = max(800, len(full_text) // 4)
            chunks = [full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size)]
            for c_idx, chunk in enumerate(chunks[:5]):
                first_line = chunk.strip().split("\n")[0][:60] if chunk.strip() else f"Core Concepts Part {c_idx+1}"
                raw_chapters.append({
                    "chapter_id": c_idx + 1,
                    "title": f"Chapter {c_idx + 1}: {first_line}",
                    "content": chunk.strip()
                })

        return raw_chapters
