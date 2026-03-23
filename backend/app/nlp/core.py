"""NLP core utilities — tokenization, TF-IDF, cosine similarity, keyphrase extraction."""

from __future__ import annotations

import math
import re
from collections import Counter

# ---------------------------------------------------------------------------
# Stopwords
# ---------------------------------------------------------------------------

STOPWORDS: frozenset[str] = frozenset(
    {
        # articles / determiners
        "a",
        "an",
        "the",
        # conjunctions
        "and",
        "or",
        "but",
        "nor",
        "so",
        "yet",
        "for",
        "although",
        "because",
        "since",
        "unless",
        "until",
        "whether",
        "while",
        "after",
        "before",
        "when",
        # prepositions
        "at",
        "by",
        "in",
        "of",
        "on",
        "to",
        "up",
        "as",
        "from",
        "into",
        "onto",
        "with",
        "about",
        "above",
        "across",
        "against",
        "along",
        "among",
        "around",
        "behind",
        "below",
        "beneath",
        "beside",
        "between",
        "beyond",
        "down",
        "during",
        "inside",
        "near",
        "off",
        "out",
        "outside",
        "over",
        "past",
        "through",
        "throughout",
        "under",
        "underneath",
        "upon",
        "within",
        "without",
        # pronouns
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "her",
        "hers",
        "herself",
        "it",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        # auxiliaries / modals
        "is",
        "am",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        # common fillers
        "also",
        "just",
        "more",
        "most",
        "than",
        "then",
        "there",
        "here",
        "where",
        "how",
        "why",
        "all",
        "any",
        "each",
        "few",
        "both",
        "very",
        "too",
        "such",
        "own",
        "same",
        "other",
        "no",
        "not",
        "only",
        "so",
        "s",
        "t",
        "don",
        "re",
        "ve",
        "ll",
        "ain",
        "wasn",
        "weren",
        "hasn",
        "hadn",
        "doesn",
        "didn",
        "couldn",
        "wouldn",
        "shouldn",
        "aren",
        "isn",
        "won",
        # job-posting noise words (ubiquitous, low signal)
        "job",
        "position",
        "role",
        "opportunity",
        "looking",
        "seeking",
        "join",
        "team",
        "company",
        "work",
        "working",
        "help",
        "make",
        "use",
        "using",
        "able",
        "well",
        "new",
        "including",
        "etc",
        "get",
        "com",
        "www",
        "strong",
        "good",
        "great",
        "excellent",
        "us",
        "if",
        "like",
    }
)

# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_WORD_RE = re.compile(r"[a-z]+")


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alpha characters, remove stopwords and single chars."""
    if not text:
        return []
    tokens = _WORD_RE.findall(text.lower())
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


# ---------------------------------------------------------------------------
# Frequency map
# ---------------------------------------------------------------------------


def build_freq_map(tokens: list[str]) -> dict[str, int]:
    """Build a term-frequency dictionary from a token list."""
    if not tokens:
        return {}
    return dict(Counter(tokens))


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------


def cosine_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse frequency/weight vectors.

    Returns a float in [0.0, 1.0].
    """
    if not a or not b:
        return 0.0

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


def tfidf_vectors(corpus: list[str]) -> list[dict[str, float]]:
    """Compute TF-IDF vectors for a list of documents.

    TF  = term count / total terms in document
    IDF = log(N / (df + 1))  (smoothed)
    """
    if not corpus:
        return []

    n = len(corpus)
    token_lists = [tokenize(doc) for doc in corpus]

    # document-frequency count
    df: dict[str, int] = {}
    for tokens in token_lists:
        for term in set(tokens):
            df[term] = df.get(term, 0) + 1

    vectors: list[dict[str, float]] = []
    for tokens in token_lists:
        total = len(tokens)
        if total == 0:
            vectors.append({})
            continue
        freq = Counter(tokens)
        vec: dict[str, float] = {}
        for term, cnt in freq.items():
            tf = cnt / total
            idf = math.log(n / (df.get(term, 0) + 1))
            vec[term] = tf * idf
        vectors.append(vec)

    return vectors


def compute_tfidf_similarity(text_a: str, text_b: str) -> float:
    """Compute TF-IDF-based cosine similarity between two text strings.

    Returns a float in [0.0, 1.0].
    """
    if not text_a or not text_b:
        return 0.0

    vectors = tfidf_vectors([text_a, text_b])
    if len(vectors) < 2:
        return 0.0

    return cosine_similarity(vectors[0], vectors[1])


# ---------------------------------------------------------------------------
# Keyphrase extraction
# ---------------------------------------------------------------------------


def extract_keyphrases(text: str, top_n: int = 10) -> list[str]:
    """Extract top-N keyphrases from text by term frequency after stopword removal."""
    if not text or not text.strip():
        return []

    tokens = tokenize(text)
    if not tokens:
        return []

    freq = Counter(tokens)
    return [term for term, _ in freq.most_common(top_n)]
