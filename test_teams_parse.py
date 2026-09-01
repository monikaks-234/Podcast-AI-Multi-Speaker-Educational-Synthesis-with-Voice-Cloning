import re

sample_text = """
Anirban Dasgupta
0 minutes 4 seconds0:04
Anirban Dasgupta 0 minutes 4 seconds
All those things are pending, and I've also started my Capstone Two; we have discussed the idea 
with, like, what this is?

Dr. Shinu Abhi
0 minutes 17 seconds0:17
Dr. Shinu Abhi 0 minutes 17 seconds
Doctor Soumya, Soumya Mehdi, you forgot his name, huh?

Santosh Kumar Singh
1 hour 27 minutes 18 seconds1:27:18
Santosh Kumar Singh 1 hour 27 minutes 18 seconds
Yeah, ma'am, actually I have not started, but I made the first slide.
"""

def parse_teams_transcript(text):
    # Regex to clean up MS Teams transcript timestamps and duplicate lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    speaker_turns = []
    
    current_speaker = None
    current_text = []
    
    for line in lines:
        # Ignore timestamp patterns like "0 minutes 4 seconds", "1 hour 27 minutes 12 seconds", "0:04"
        if re.search(r'^\d+\s*(minutes|seconds|hour|hours)|^\d+:\d+', line, re.IGNORECASE):
            continue
            
        # Check if line looks like a speaker name (e.g., Dr. Shinu Abhi, Anirban Dasgupta, Santosh Kumar Singh)
        if re.match(r'^(Dr\.|Prof\.|Mr\.|Ms\.)?\s*[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', line):
            if current_speaker and current_text:
                speaker_turns.append({
                    "speaker": current_speaker,
                    "text": " ".join(current_text)
                })
                current_text = []
            current_speaker = line
        else:
            if current_speaker:
                # Avoid repeating the speaker's name in text
                if not line.startswith(current_speaker):
                    current_text.append(line)
                    
    if current_speaker and current_text:
        speaker_turns.append({
            "speaker": current_speaker,
            "text": " ".join(current_text)
        })
        
    return speaker_turns

turns = parse_teams_transcript(sample_text)
print(f"Extracted {len(turns)} turns:")
for t in turns:
    print(t)
