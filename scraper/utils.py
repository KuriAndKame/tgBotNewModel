def extract_title_and_summary(text):
    if not text:
        return None, None
    lines = text.strip().split('\n')
    title = lines[0][:200]
    summary = lines[1][:300] if len(lines) > 1 else None
    return title, summary
