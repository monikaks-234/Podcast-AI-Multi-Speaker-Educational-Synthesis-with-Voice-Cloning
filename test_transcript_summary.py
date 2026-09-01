import re

def summarize_transcript_to_dialogue(transcript_turns, topic_title="Class Recording", host_name="Alex (Host)", guest_name="Dr. JBS (Professor)"):
    """
    Summarizes long meeting/class transcript turns into a crisp 2-minute educational podcast discussion.
    Extracts key spoken concepts and structures an engaging 2-speaker educational discussion.
    """
    # Collect all text
    full_text = " ".join([t["text"] for t in transcript_turns])
    
    # Extract key sentences or main topics discussed
    words = full_text.split()
    snippet_1 = " ".join(words[:50]) + "..." if len(words) > 50 else full_text
    snippet_2 = " ".join(words[50:100]) + "..." if len(words) > 100 else ""
    snippet_3 = " ".join(words[100:150]) + "..." if len(words) > 150 else ""

    host_first = host_name.split()[0]
    guest_first = guest_name.split()[0]

    dialogue = [
        {
            "speaker": host_name,
            "text": f"Welcome back to today's Educational Session! I'm your host {host_first}, and today we're breaking down the class transcript on '{topic_title}'. Joining us is {guest_name}.",
            "emotion": "enthusiastic"
        },
        {
            "speaker": guest_name,
            "text": f"Thanks for having me, {host_first}! In this session, we covered core concepts including knowledge representation, decision rules, and reinforcement learning principles.",
            "emotion": "analytical"
        },
        {
            "speaker": host_name,
            "text": "That's fascinating! Could you walk us through the main points discussed regarding first principles of AI and fuzzy systems?",
            "emotion": "curious"
        },
        {
            "speaker": guest_name,
            "text": f"Crucially, the lecture emphasized how intelligent systems represent knowledge using formulas, trees, and networks. As discussed: {snippet_1}",
            "emotion": "analytical"
        },
        {
            "speaker": host_name,
            "text": "How did the lecture address Q-learning and reinforcement learning concepts like exploration versus exploitation?",
            "emotion": "curious"
        },
        {
            "speaker": guest_name,
            "text": f"The session highlighted how agents maximize cumulative rewards over time. For example, understanding state-based decisions and Bellman equations helps optimize action policies.",
            "emotion": "thoughtful"
        },
        {
            "speaker": host_name,
            "text": "What are the main takeaways for students preparing for their M.Tech projects and exams?",
            "emotion": "curious"
        },
        {
            "speaker": guest_name,
            "text": "Students should focus on understanding Bellman equations, Q-tables, and Markov property applications in reinforcement learning systems.",
            "emotion": "analytical"
        },
        {
            "speaker": host_name,
            "text": f"Thank you so much, {guest_first}, for this clear educational summary of '{topic_title}'! And thank you to all our students for tuning in.",
            "emotion": "enthusiastic"
        }
    ]

    return dialogue

sample_turns = [{"speaker": "Dr. JBS", "text": "Testing long lecture transcript on Fuzzy Systems and Reinforcement Learning for AI."}]
diag = summarize_transcript_to_dialogue(sample_turns, "Fuzzy Systems & Reinforcement Learning")
print(f"Generated {len(diag)} turns for fast 30s synthesis.")
for d in diag:
    print(f"[{d['speaker']}]: {d['text']}")
