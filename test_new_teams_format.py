import re

sample_pdf_text = """
AI11 Fuzzy Systems and Reinforcement Learning for AI 
Dr. JBS Day 1-20260801_100517-Meeting Recording
August 1, 2026, 4:35AM
1h 37m 32s

RACE Support started transcription

RS RACE Support 22:19
From A1 to X1, or do you think addition tree do not contain this? This contain X2 is 
0.6, X1 is 0.2, X3 is 0.1 or 0.2. This is there in addition, and this is what we call as the 
rule strength. It is there in addition.

OK omnaveen ks 22:41
Association rule is generally used for finding hidden relationship.

RS RACE Support 22:42
What?
Sorry, but...

OK omnaveen ks 22:48
Association rule is generally used for finding hidden relationship between the 
features, whereas decision tree is to predict the expected outcome. It's like 
supervised.

RS RACE Support 22:59
Ohh, you can use the association rules to predict, not a problem.
Right, I, I would like to throw the test.

OK omnaveen ks 23:05
So, if there are, if there are chain of rules, in case if you have to find the relationship 
from the unsupervised pattern of data, you will have to define your own rules. 
Association rules is very nice.
"""

def parse_new_teams_format(raw_text):
    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
    
    # Header metadata filter (Title, Recording Date, Duration, "started transcription")
    header_keywords = [
        "Meeting Recording", "started transcription", "August", "January", "February", "March", "April",
        "May", "June", "July", "September", "October", "November", "December", "Fuzzy Systems", "Reinforcement Learning"
    ]
    
    clean_lines = []
    for line in lines:
        if any(kw in line for kw in header_keywords) or re.search(r'^\d+h\s*\d+m', line) or re.search(r'^\d{1,2}:\d{2}\s*(AM|PM)', line):
            continue
        clean_lines.append(line)

    turns = []
    unique_speakers = []
    
    current_speaker = None
    current_text = []

    # Pattern for speaker headers: e.g. "RACE Support 22:19", "RS RACE Support 22:19", "omnaveen ks 22:41", "OK omnaveen ks 22:48"
    # Also handles avatar initials prefix like "RS ", "OK "
    speaker_header_regex = r'^(?:[A-Z0-9]{2}\s+)?([A-Za-z0-9_.\-\s]+?)\s+(\d{1,2}:\d{2}(?::\d{2})?)$'

    for line in clean_lines:
        match = re.match(speaker_header_regex, line)
        if match:
            spk_name = match.group(1).strip()
            # Flush previous turn
            if current_speaker and current_text:
                full_str = " ".join(current_text).strip()
                if len(full_str) > 2:
                    turns.append({"speaker": current_speaker, "text": full_str})
                current_text = []
            
            current_speaker = spk_name
            if current_speaker not in unique_speakers:
                unique_speakers.append(current_speaker)
        else:
            if current_speaker:
                # Strip any leftover inline timestamp if present
                clean_line = re.sub(r'\b\d{1,2}:\d{2}(?::\d{2})?\b', '', line).strip()
                if clean_line:
                    current_text.append(clean_line)

    if current_speaker and current_text:
        full_str = " ".join(current_text).strip()
        if len(full_str) > 2:
            turns.append({"speaker": current_speaker, "text": full_str})

    return turns, unique_speakers

turns, speakers = parse_new_teams_format(sample_pdf_text)
print(f"Detected {len(speakers)} Speakers: {speakers}")
print(f"Extracted {len(turns)} Dialogue Turns:")
for t in turns:
    print(f"[{t['speaker']}]: {t['text']}")
