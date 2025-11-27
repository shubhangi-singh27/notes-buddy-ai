def chunk_text(text, max_tokens=500, overlap=50):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + max_tokens
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)

        start = end - overlap
        if start<0:
            start = 0

    return chunks