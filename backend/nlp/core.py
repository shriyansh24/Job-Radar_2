"""NLP core utilities — tokenization, TF-IDF, cosine similarity, keyphrase extraction."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Dict, List

# ---------------------------------------------------------------------------
# Stopwords
# ---------------------------------------------------------------------------

STOPWORDS: frozenset[str] = frozenset({
    # articles / determiners
    "a", "an", "the",
    # conjunctions
    "and", "or", "but", "nor", "so", "yet", "for",
    "although", "because", "since", "unless", "until",
    "whether", "while", "after", "before", "when",
    # prepositions
    "at", "by", "in", "of", "on", "to", "up", "as",
    "at", "from", "into", "onto", "with", "about",
    "above", "across", "against", "along", "among",
    "around", "before", "behind", "below", "beneath",
    "beside", "between", "beyond", "down", "during",
    "inside", "near", "off", "out", "outside", "over",
    "past", "since", "through", "throughout", "under",
    "underneath", "until", "upon", "within", "without",
    # pronouns
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself",
    "she", "her", "hers", "herself",
    "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves",
    "what", "which", "who", "whom", "this", "that",
    "these", "those",
    # auxiliaries / modals
    "is", "am", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "having",
    "do", "does", "did", "doing",
    "will", "would", "could", "should", "may", "might",
    "must", "shall", "can",
    # common fillers
    "also", "just", "more", "most", "than", "then",
    "there", "here", "where", "how", "why", "all", "any",
    "each", "few", "both", "very", "too", "such", "own",
    "same", "other", "no", "not", "only", "same", "so",
    "than", "too", "very", "s", "t", "don",
    "re", "ve", "ll", "ain", "wasn", "weren", "hasn",
    "hadn", "doesn", "didn", "couldn", "wouldn", "shouldn",
    "aren", "isn", "won",
    # job-posting noise words (ubiquitous, low signal)
    "job", "position", "role", "opportunity", "looking",
    "seeking", "join", "team", "company", "work", "working",
    "help", "make", "use", "using", "able", "well", "across",
    "new", "including", "etc", "get", "com", "www",
    "strong", "good", "great", "excellent",
    "us", "if", "like",
})

# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z]+")


def tokenize(text: str) -> List[str]:
    """Lowercase, split on non-alpha characters, remove stopwords and single chars.

    Args:
        text: Raw text string to tokenize.

    Returns:
        List of meaningful lowercase word tokens.
    """
    if not text:
        return []
    tokens = _WORD_RE.findall(text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


# ---------------------------------------------------------------------------
# Frequency map
# ---------------------------------------------------------------------------


def build_freq_map(tokens: List[str]) -> Dict[str, int]:
    """Build a term-frequency dictionary from a token list.

    Args:
        tokens: List of string tokens.

    Returns:
        Dict mapping each token to its occurrence count.
    """
    if not tokens:
        return {}
    return dict(Counter(tokens))


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------


def cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Compute cosine similarity between two sparse frequency/weight vectors.

    Args:
        a: First vector as {term: weight}.
        b: Second vector as {term: weight}.

    Returns:
        Cosine similarity in [0.0, 1.0].  Returns 0.0 if either vector is empty.
    """
    if not a or not b:
        return 0.0

    # dot product over shared keys only (sparse)
    dot = sum(a[k] * b[k] for k in a if k in b)
    if dot == 0.0:
        return 0.0

    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# TF-IDF vectorizer
# ---------------------------------------------------------------------------


def tfidf_vectors(corpus: List[str]) -> List[Dict[str, float]]:
    """Compute TF-IDF vectors for a list of documents.

    TF  = term count / total terms in document
    IDF = log( N / (df + 1) )   (smoothed to avoid division by zero)

    Args:
        corpus: List of raw text strings.

    Returns:
        List of dicts, one per document, mapping term → TF-IDF weight.
        Empty list if corpus is empty.
    """
    if not corpus:
        return []

    n = len(corpus)
    # tokenize every document once
    token_lists = [tokenize(doc) for doc in corpus]

    # document-frequency count: how many docs contain each term
    df: Dict[str, int] = {}
    for tokens in token_lists:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    vectors: List[Dict[str, float]] = []
    for tokens in token_lists:
        total = len(tokens)
        if total == 0:
            vectors.append({})
            continue
        freq = Counter(tokens)
        vec: Dict[str, float] = {}
        for term, cnt in freq.items():
            tf = cnt / total
            idf = math.log(n / (df.get(term, 0) + 1))
            vec[term] = tf * idf
        vectors.append(vec)

    return vectors


# ---------------------------------------------------------------------------
# Keyphrase extraction
# ---------------------------------------------------------------------------


def compute_tfidf_similarity(text_a: str, text_b: str) -> float:
    """Compute TF-IDF-based cosine similarity between two text strings.

    A lightweight 2-document TF-IDF computation:
    1. Tokenize both texts.
    2. Build a mini IDF from the 2-document corpus.
    3. Compute TF-IDF vectors for each document.
    4. Return cosine similarity of the two vectors.

    Returns a float in [0.0, 1.0].  Returns 0.0 for empty inputs.

    Args:
        text_a: First raw text string (e.g. resume).
        text_b: Second raw text string (e.g. job description).
    """
    if not text_a or not text_b:
        return 0.0

    vectors = tfidf_vectors([text_a, text_b])
    if len(vectors) < 2:
        return 0.0

    return cosine_similarity(vectors[0], vectors[1])


def extract_keyphrases(text: str, top_n: int = 10) -> List[str]:
    """Extract top-N keyphrases from text by simple term frequency after stopword removal.

    Args:
        text: Raw input text.
        top_n: Maximum number of keyphrases to return.

    Returns:
        List of top-N tokens ordered by descending frequency.
        Returns empty list for empty/blank input.
    """
    if not text or not text.strip():
        return []

    tokens = tokenize(text)
    if not tokens:
        return []

    freq = Counter(tokens)
    return [term for term, _ in freq.most_common(top_n)]
