import re
import tiktoken
from typing import List

MAX_CHUNK_TOKENS = 900
MIN_CHUNK_TOKENS = 300
OVERLAP_RATIO = 0.15
MODEL_NAME = "text-embedding-3-small"

encoding = tiktoken.encoding_for_model(MODEL_NAME)

def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(encoding.encode(text))

def normalize_text(text: str) -> str:
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def split_paragraphs(text: str) -> List[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]

def split_sentences(text: str) -> List[str]:
    """ Split text into sentences while preserving sentence boundaries"""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]

def split_oversized_paragraphs(paragraph: str) -> List[str]:
    """Split a paragraph that exceeds MAX_CHUNK_TOKENS into smaller chunks"""
    sentences = split_sentences(paragraph)
    if not sentences:
        return [paragraph[:MAX_CHUNK_TOKENS]]

    sub_paragraphs = []
    current_sub = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        # if single sentence exceeds MAX_CHUNK_TOKENS, truncate it
        if sentence_tokens > MAX_CHUNK_TOKENS:
            # save current sub-paragraph if any
            if current_sub:
                sub_paragraphs.append(" ".join(current_sub))
                current_sub = []
                current_tokens = 0

            # truncate oversized sentence
            truncated = encoding.decode(
                encoding.encode(sentence)[:MAX_CHUNK_TOKENS]
            )
            sub_paragraphs.append(truncated)
            continue
        
        # check if adding sentence exceed max tokens
        if current_tokens + sentence_tokens <= MAX_CHUNK_TOKENS:
            current_sub.append(sentence)
            current_tokens += sentence_tokens
        else:
            # save current sub-paragraph if any
            if current_sub:
                sub_paragraphs.append(" ".join(current_sub))

            # start new sub_paragraph with this sentence
            current_sub = [sentence]
            current_tokens = sentence_tokens

    if current_sub:
        sub_paragraphs.append(" ".join(current_sub))

    return sub_paragraphs

def chunk_text(text) -> List[str]:
    text = normalize_text(text)
    paragraphs = split_paragraphs(text)

    if not paragraphs:
        return []

    chunks = []
    current_chunk = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = count_tokens(paragraph)

        """if paragraph_tokens > MAX_CHUNK_TOKENS:
            paragraph = encoding.decode(
                encoding.encode(paragraph)[:MAX_CHUNK_TOKENS]
            )
            paragraph_tokens = count_tokens(paragraph)"""
        
        # let's try to split oversized paragraphs
        if paragraph_tokens > MAX_CHUNK_TOKENS:
            sub_paragraphs = split_oversized_paragraphs(paragraph)
            # process each sub paragraph
            for sub_para in sub_paragraphs:
                sub_para_tokens = count_tokens(sub_para)

                if current_tokens + sub_para_tokens <= MAX_CHUNK_TOKENS:
                    current_chunk.append(sub_para)
                    current_tokens += sub_para_tokens
                else:
                    if current_chunk:
                        chunks.append("\n\n".join(current_chunk))

                    overlap_tokens_target = int(MAX_CHUNK_TOKENS * OVERLAP_RATIO)
                    overlap_paragraphs = []
                    overlap_tokens = 0

                    for p in reversed(current_chunk):
                        p_tokens = count_tokens(p)
                        if overlap_tokens + p_tokens > overlap_tokens_target:
                            break
                        overlap_paragraphs.insert(0, p)
                        overlap_tokens += p_tokens

                    current_chunk = overlap_paragraphs + [sub_para]
                    current_tokens = sum(count_tokens(p) for p in current_chunk)
            continue
        # end of try to split oversized paragraphs

        if current_tokens + paragraph_tokens <= MAX_CHUNK_TOKENS:
            current_chunk.append(paragraph)
            current_tokens += paragraph_tokens
        else:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))

            overlap_tokens_target = int(MAX_CHUNK_TOKENS * OVERLAP_RATIO)
            overlap_paragraphs = []
            overlap_tokens = 0

            for p in reversed(current_chunk):
                p_tokens = count_tokens(p)
                if overlap_tokens + p_tokens > overlap_tokens_target:
                    break
                overlap_paragraphs.insert(0, p)
                overlap_tokens += p_tokens

            current_chunk = overlap_paragraphs + [paragraph]
            current_tokens = sum(count_tokens(p) for p in current_chunk)

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    if len(chunks) >= 2:
        last_chunk_tokens = count_tokens(chunks[-1])
        if last_chunk_tokens < MIN_CHUNK_TOKENS:
            chunks[-2] = chunks[-2] + "\n\n" + chunks[-1]
            chunks.pop()

    return chunks