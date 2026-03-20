import re
import logging
from typing import List, Dict, Any

import tiktoken

logger = logging.getLogger("search")


################### CONFIGURATION ###################
MAX_TOTAL_TOKENS = 3000
MIN_SENTENCE_PER_CHUNK = 2

WEIGHTS = {
    "keyword": 0.5,
    "embedding": 0.4,
    "position": 0.1
}

OPEN_AI_MODEL = "gpt-4o-mini"

STOPWORDS = {
    "the", "is", "are", "a", "an", "of", "in", "on",
    "and", "or", "to", "for", "with", "by", "from",
    "that", "this", "it", "as", "at", "be", "was",
    "were", "which", "what", "when", "where", "how",
    "why", "who"
}

encoding = tiktoken.encoding_for_model(OPEN_AI_MODEL)


################### TOKEN UTILITIES ###################

def count_tokens(text: str) -> int:
    if not text:
        return 0

    return len(encoding.encode(text))

################### TEXT UTILITIES ###################

def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def split_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]

def tokenize_words(text: str) -> List[str]:
    words = re.findall(r"\b\w+\b", text.lower())
    return [w for w in words if w not in STOPWORDS]


################### SCORING ###################

def score_sentence(
    sentence: str,
    sentence_index: int,
    question_tokens: set,
    chunk_similarity: float
) -> float:
    
    sentence_tokens = set(tokenize_words(sentence))
    if not sentence_tokens:
        keyword_score = 0.0

    else:
        overlap = question_tokens.intersection(sentence_tokens)
        keyword_score = len(overlap) / max(len(sentence_tokens), 1)

    positional_score = 1.0 / (sentence_index+1)

    final_score = (
        WEIGHTS["keyword"] * keyword_score
        + WEIGHTS["embedding"] * chunk_similarity
        + WEIGHTS["position"] * positional_score
    )

    return final_score


################### COMPRESSION FUNCTION ###################

def compress_context(
    chunks: List[Dict[str, Any]],
    question: str,
    question_vector: List[float] = None
) -> List[Dict[str, Any]]:

    if not chunks:
        return []

    question_tokens = set(tokenize_words(question))

    num_chunks = len(chunks)
    max_per_chunk_tokens = min(
        800, max(300, MAX_TOTAL_TOKENS//(max(num_chunks, 1)))
    )

    total_tokens_before = sum(count_tokens(c["text"]) for c in chunks)

    compressed_chunks = []
    total_tokens_after = 0

    for chunk in chunks:
        original_text = normalize_text(chunk.get("text", ""))
        chunk_similarity = float(chunk.get("similarity", 0.0))

        if not original_text:
            continue

        original_token_count = count_tokens(original_text)

        if original_token_count <= max_per_chunk_tokens:
            compressed_chunks.append(chunk)
            total_tokens_after += original_token_count

            continue

        sentences = split_sentences(original_text)

        if not sentences:
            continue

        scored_sentences = []

        for idx, sentence in enumerate(sentences):
            score = score_sentence(sentence, idx, question_tokens, chunk_similarity)
            scored_sentences.append((idx, sentence, score))

        scored_sentences.sort(key=lambda x:x[2], reverse=True)

        selected_sentences = []
        selected_token_count = 0

        for idx, sentence, socre in scored_sentences[:MIN_SENTENCE_PER_CHUNK]:
            sentence_tokens = count_tokens(sentence)
            selected_sentences.append((idx, sentence, score))
            selected_token_count += sentence_tokens

        for idx, sentence, score in scored_sentences[MIN_SENTENCE_PER_CHUNK:]:
            sentence_tokens = count_tokens(sentence)
            if selected_token_count + sentence_tokens > max_per_chunk_tokens:
                continue

            selected_sentences.append((idx, sentence, score))
            selected_token_count += sentence_tokens

        selected_sentences.sort(key=lambda x: x[0])
        compressed_text = " ".join(s[1] for s in selected_sentences)

        compressed_chunk = chunk.copy()
        compressed_chunk["text"] = compressed_text

        compressed_chunks.append(compressed_chunk)
        total_tokens_after += count_tokens(compressed_text)


    if total_tokens_after > MAX_TOTAL_TOKENS:
        compressed_chunks.sort(key=lambda c: c.get("similarity", 0.0))

        trimmed_chunks = []
        running_total = 0

        for chunk in reversed(compressed_chunks):
            chunk_tokens = count_tokens(chunk["text"])

            if running_total + chunk_tokens > MAX_TOTAL_TOKENS:
                continue

            trimmed_chunks.append(chunk)
            running_total += chunk_tokens

        compressed_chunks = trimmed_chunks
        total_tokens_after = running_total

    if total_tokens_before > 0:
        reduction = ((total_tokens_before - total_tokens_after)/total_tokens_before)*100
    else:
        reduction = 0.0

    logger.info(
        "[compression] tokens_before=%s tokens_after=%s reduction=%.2f%%",
        total_tokens_before,
        total_tokens_after,
        reduction,
    )
    
    return compressed_chunks