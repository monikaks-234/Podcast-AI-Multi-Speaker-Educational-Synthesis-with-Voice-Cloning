import json, os

history_path = "outputs/history.json"
if os.path.exists(history_path):
    with open(history_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for item in data:
        mode = item.get("mode", "")
        if "Research" in mode or "Paper" in mode or "Breakdown" in mode:
            if item.get("speakers") and len(item.get("speakers")) > 2:
                item["mode"] = "Educational Class Transcript"
            else:
                item["mode"] = "General Podcast Topic"

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Sanitized history.json! Removed all Research Paper Breakdown legacy strings.")
