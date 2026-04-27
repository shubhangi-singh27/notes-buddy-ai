import re
import logging
from typing import List, Dict, Any
from collections import defaultdict
import random
import tiktoken

logger = logging.getLogger("search")


################### CONFIGURATION ###################
MAX_TOTAL_TOKENS = 3000

WINDOW_SIZE = 3

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
) -> float:
    
    sentence_tokens = set(tokenize_words(sentence))
    if not sentence_tokens:
        return 0.0

    overlap = question_tokens.intersection(sentence_tokens)
    keyword_density = len(overlap) / (len(sentence_tokens) ** 0.5)
    # High density → focused sentence, Low density → noisy sentence
    keyword_coverage = len(overlap) / max(len(question_tokens), 1)  
    # High coverage → sentence answers more of the question, Low coverage → partial match

    keyword_score = 0.7 * keyword_density + 0.3 * keyword_coverage

    positional_score = 1.0 / (0.1 * sentence_index + 1)

    final_score = (
        0.75 * keyword_score
        + 0.25 * positional_score
    )

    return final_score


################### COMPRESSION FUNCTION ###################

def compress_context(
    chunks: List[Dict[str, Any]],
    question: str,
    question_vector: List[float] = None
) -> tuple[list[dict[str, Any]], int, int]:

    if not chunks:
        return [], 0, 0

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
        # chunk_similarity = float(chunk.get("similarity", 0.0))

        if not original_text:
            continue

        original_token_count = count_tokens(original_text)

        if original_token_count <= max_per_chunk_tokens:
            compressed_chunks.append(chunk)
            total_tokens_after += original_token_count

            continue

        sentences = split_sentences(original_text)
        sentence_tokens = [count_tokens(s) for s in sentences]

        if not sentences:
            continue

        scored_sentences = []

        for idx, sentence in enumerate(sentences):
            score = score_sentence(sentence, idx, question_tokens)
            scored_sentences.append(score)

        windows = []
        for i in range(len(sentences)):
            window_sentences = sentences[i: i+WINDOW_SIZE]
            if not window_sentences:
                continue

            window_tokens = sum(sentence_tokens[i: i+WINDOW_SIZE])

            if window_tokens > max_per_chunk_tokens:
                continue
            
            window_text = " ".join(window_sentences)

            window_scores = scored_sentences[i: i+WINDOW_SIZE]
            window_score = (
                (sum(window_scores) / len(window_scores))
                * (1 + 0.1 * chunk.get("similarity", 0.0))
            )
            windows.append((i, window_text, window_score, window_tokens))

        windows.sort(key=lambda x: x[2], reverse=True)

        selected_token_count = 0
        selected_windows = []

        selected_indices = set()
        for start_idx, text, score, tokens in windows:
            window_range = set(range(start_idx, start_idx + WINDOW_SIZE))

            if selected_indices.intersection(window_range):
                continue

            if selected_token_count + tokens > max_per_chunk_tokens:
                continue
            
            selected_windows.append((start_idx, text))
            selected_token_count += tokens
            selected_indices.update(window_range)

        selected_windows.sort(key=lambda x: x[0])

        if not selected_windows:
            compressed_text = " ".join(sentences[:WINDOW_SIZE])
        else:
            compressed_text = " ".join(w[1] for w in selected_windows)

        compressed_chunk = chunk.copy()
        compressed_chunk["text"] = compressed_text

        compressed_chunk["compression_meta"] = {
            "method": "window",
            "window_size": WINDOW_SIZE,
            "tokens": selected_token_count
        }

        compressed_chunks.append(compressed_chunk)
        total_tokens_after += compressed_chunk["compression_meta"].get(
            "tokens",
            count_tokens(chunk["text"])
        )


    if total_tokens_after > MAX_TOTAL_TOKENS:
        compressed_chunks.sort(key=lambda c: c.get("similarity", 0.0))

        doc_groups = defaultdict(list)

        for chunk in compressed_chunks:
            doc_groups[chunk["document_id"]].append(chunk)
        
        for doc_id in doc_groups:
            doc_groups[doc_id].sort(key=lambda x: x["similarity"], reverse=True)

        trimmed_chunks = []
        running_total = 0

        doc_ids = list(doc_groups.keys())
        random.shuffle(doc_ids)
        pointers = {doc_id: 0 for doc_id in doc_ids} # pointers to each document in the trimmed chunks

        while True:
            added = False

            for doc_id in doc_ids:
                idx = pointers[doc_id]
                # check if we have picked all chunks sent for compression from this document
                if idx >= len(doc_groups[doc_id]):
                    continue 

                chunk = doc_groups[doc_id][idx]
                chunk_tokens = chunk["compression_meta"].get(
                    "tokens",
                    count_tokens(chunk["text"])
                )

                if running_total + chunk_tokens <= MAX_TOTAL_TOKENS:
                    trimmed_chunks.append(chunk)
                    running_total += chunk_tokens
                    pointers[doc_id] += 1   # if chunk is added then increment the pointer to doc_id
                    added = True

                
            if not added:
                break

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
    
    return compressed_chunks, total_tokens_before, total_tokens_after