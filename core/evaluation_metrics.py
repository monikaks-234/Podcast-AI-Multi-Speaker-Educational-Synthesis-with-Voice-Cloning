import re
from typing import List, Dict, Any

class EvaluationMetrics:
    """
    Computes academic evaluation metrics for script quality,
    conversational balance, readability scores, and pedagogical stats.
    """

    @staticmethod
    def count_syllables(word: str) -> int:
        """Estimates syllable count using standard English vowel pattern rules."""
        word = word.lower().strip()
        if not word:
            return 1
        if len(word) <= 3:
            return 1
        # Remove trailing silent 'e', 'es', 'ed'
        word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
        syllables = len(re.findall(r'[aeiouy]{1,2}', word))
        return max(1, syllables)

    @staticmethod
    def analyze_script_metrics(dialogue: List[Dict[str, str]]) -> Dict[str, Any]:
        """Calculates script quality, readability & conversational metrics for any mode."""
        if not dialogue:
            return {
                "total_dialogue_turns": 0,
                "total_word_count": 0,
                "host_word_pct": 50.0,
                "guest_word_pct": 50.0,
                "lexical_diversity_ttr": 0.0,
                "flesch_reading_ease": 75.0,
                "flesch_kincaid_grade": 8.0,
                "reading_ease_label": "Standard",
                "conversational_quality_grade": "A",
                "speaker_distribution": []
            }

        speaker_word_counts = {}
        all_words = []
        sentence_count = 0
        total_syllables = 0

        for turn in dialogue:
            raw_speaker = turn.get("speaker", "Speaker").strip()
            text = turn.get("text", "").strip()

            words = re.findall(r'\b[a-zA-Z0-9\'-]+\b', text.lower())
            sentences = [s for s in re.split(r'[.!?]+', text) if s.strip()]

            all_words.extend(words)
            sentence_count += max(len(sentences), 1)

            # Syllable counting
            for w in words:
                total_syllables += EvaluationMetrics.count_syllables(w)

            speaker_word_counts[raw_speaker] = speaker_word_counts.get(raw_speaker, 0) + len(words)

        total_words = len(all_words)
        unique_words = len(set(all_words))

        # 1. Lexical Diversity (TTR - Type-Token Ratio)
        ttr_score = round(unique_words / max(total_words, 1), 3)

        # 2. Readability Metrics (Flesch Reading Ease & Flesch-Kincaid Grade Level)
        avg_sentence_len = total_words / max(sentence_count, 1)
        avg_syllables_per_word = total_syllables / max(total_words, 1)

        flesch_reading_ease = 206.835 - (1.015 * avg_sentence_len) - (84.6 * avg_syllables_per_word)
        flesch_reading_ease = round(max(0.0, min(100.0, flesch_reading_ease)), 1)

        fk_grade = (0.39 * avg_sentence_len) + (11.8 * avg_syllables_per_word) - 15.59
        fk_grade = round(max(1.0, min(18.0, fk_grade)), 1)

        if flesch_reading_ease >= 80:
            reading_label = "Very Easy (High Engagement)"
        elif flesch_reading_ease >= 65:
            reading_label = "Standard Conversational"
        elif flesch_reading_ease >= 50:
            reading_label = "Undergraduate / Academic"
        else:
            reading_label = "Advanced Technical"

        # 3. Speaker Balance Distribution
        speaker_distribution = []
        host_words = 0
        guest_words = 0
        first_speaker_seen = None

        for spk, cnt in speaker_word_counts.items():
            pct = round((cnt / max(total_words, 1)) * 100, 1)
            speaker_distribution.append({
                "speaker": spk,
                "word_count": cnt,
                "percentage": pct
            })
            if first_speaker_seen is None:
                first_speaker_seen = spk

            spk_lower = spk.lower()
            is_secondary = any(k in spk_lower for k in ["guest", "expert", "alex", "professor", "simha", "faculty", "speaker 2", "dr. alex"])
            is_primary = any(k in spk_lower for k in ["host", "student", "monika", "speaker 1"])

            if is_secondary:
                guest_words += cnt
            elif is_primary:
                host_words += cnt
            elif spk == first_speaker_seen:
                host_words += cnt
            else:
                guest_words += cnt

        if host_words + guest_words == 0:
            host_words = total_words // 2
            guest_words = total_words - host_words

        host_pct = round((host_words / max(total_words, 1)) * 100, 1)
        guest_pct = round(100.0 - host_pct, 1)

        return {
            "total_dialogue_turns": len(dialogue),
            "total_word_count": total_words,
            "host_word_pct": host_pct,
            "guest_word_pct": guest_pct,
            "lexical_diversity_ttr": ttr_score,
            "flesch_reading_ease": flesch_reading_ease,
            "flesch_kincaid_grade": fk_grade,
            "reading_ease_label": reading_label,
            "conversational_quality_grade": "A+" if 35 <= host_pct <= 65 else "A",
            "speaker_distribution": speaker_distribution
        }
