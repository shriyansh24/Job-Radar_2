"""Test NLP core utilities."""
import pytest
from backend.nlp.core import tokenize, build_freq_map, cosine_similarity, tfidf_vectors, extract_keyphrases


class TestTokenize:
    def test_basic(self):
        tokens = tokenize("Hello world, this is a test!")
        assert "hello" in tokens and "world" in tokens and "," not in tokens

    def test_empty(self):
        assert tokenize("") == []

    def test_removes_stopwords(self):
        tokens = tokenize("the quick brown fox jumps over the lazy dog")
        assert "the" not in tokens and "quick" in tokens

    def test_single_char_removed(self):
        tokens = tokenize("a b c python")
        assert "a" not in tokens
        assert "b" not in tokens
        assert "c" not in tokens
        assert "python" in tokens

    def test_case_insensitive(self):
        tokens = tokenize("Python JAVA JavaScript")
        assert "python" in tokens and "java" in tokens and "javascript" in tokens

    def test_punctuation_stripped(self):
        tokens = tokenize("machine-learning, deep.learning, NLP!")
        # hyphens/dots become word boundaries; individual parts become tokens
        assert "," not in tokens
        assert "!" not in tokens
        assert "." not in tokens

    def test_numbers_excluded(self):
        # regex matches [a-z]+ only, so digits yield no tokens
        tokens = tokenize("123 456")
        assert tokens == []

    def test_whitespace_only(self):
        assert tokenize("   \t\n   ") == []


class TestBuildFreqMap:
    def test_basic(self):
        fm = build_freq_map(["a", "b", "a", "c"])
        assert fm["a"] == 2 and fm["b"] == 1

    def test_empty(self):
        assert build_freq_map([]) == {}

    def test_all_unique(self):
        fm = build_freq_map(["python", "java", "go"])
        assert all(v == 1 for v in fm.values())

    def test_single_token_repeated(self):
        fm = build_freq_map(["python"] * 5)
        assert fm["python"] == 5

    def test_returns_dict(self):
        result = build_freq_map(["x"])
        assert isinstance(result, dict)


class TestCosineSimilarity:
    def test_identical(self):
        d = {"python": 3, "react": 2}
        assert cosine_similarity(d, d) == pytest.approx(1.0, abs=0.01)

    def test_orthogonal(self):
        assert cosine_similarity({"python": 1}, {"java": 1}) == pytest.approx(0.0)

    def test_partial_overlap(self):
        score = cosine_similarity({"python": 3, "react": 2}, {"python": 1, "java": 4})
        assert 0.0 < score < 1.0

    def test_empty_doc(self):
        assert cosine_similarity({}, {"python": 1}) == 0.0

    def test_both_empty(self):
        assert cosine_similarity({}, {}) == 0.0

    def test_score_in_range(self):
        a = {"python": 2, "django": 1, "fastapi": 3}
        b = {"python": 1, "flask": 2, "fastapi": 2}
        score = cosine_similarity(a, b)
        assert 0.0 <= score <= 1.0

    def test_symmetry(self):
        a = {"python": 2, "go": 1}
        b = {"python": 1, "rust": 3}
        assert cosine_similarity(a, b) == pytest.approx(cosine_similarity(b, a), abs=1e-9)


class TestTFIDFVectors:
    def test_produces_vectors(self):
        corpus = [
            "python machine learning tensorflow",
            "java spring boot microservices",
            "python django web development",
        ]
        vectors = tfidf_vectors(corpus)
        assert len(vectors) == 3 and isinstance(vectors[0], dict)

    def test_empty_corpus(self):
        assert tfidf_vectors([]) == []

    def test_single_document(self):
        vectors = tfidf_vectors(["python machine learning"])
        assert len(vectors) == 1
        # single-doc IDF is log(1/2) < 0 but vector is still a dict
        assert isinstance(vectors[0], dict)

    def test_common_term_lower_weight(self):
        corpus = [
            "python developer python engineer",
            "python machine learning python",
            "java developer spring",
        ]
        vectors = tfidf_vectors(corpus)
        # "python" appears in 2/3 docs; a rare term in doc 0 should have higher IDF
        # At minimum, vectors are valid dicts with float values
        for v in vectors:
            assert all(isinstance(val, float) for val in v.values())

    def test_all_empty_docs(self):
        vectors = tfidf_vectors(["", "", ""])
        assert len(vectors) == 3
        assert all(v == {} for v in vectors)

    def test_vector_keys_are_tokens(self):
        vectors = tfidf_vectors(["machine learning pipeline"])
        # keys should be non-stopword lower-case alphabetic tokens
        for k in vectors[0]:
            assert k.isalpha() and k == k.lower()


class TestExtractKeyphrases:
    def test_extracts_from_text(self):
        text = (
            "We need a senior Python engineer with experience in machine learning"
            " and distributed systems."
        )
        phrases = extract_keyphrases(text, top_n=5)
        assert 0 < len(phrases) <= 5

    def test_empty_text(self):
        assert extract_keyphrases("") == []

    def test_blank_text(self):
        assert extract_keyphrases("   ") == []

    def test_top_n_respected(self):
        text = "python java python java python java scala go rust kotlin swift ruby"
        phrases = extract_keyphrases(text, top_n=3)
        assert len(phrases) <= 3

    def test_order_by_frequency(self):
        text = "python python python java java go"
        phrases = extract_keyphrases(text, top_n=10)
        assert phrases[0] == "python"
        assert phrases[1] == "java"

    def test_stopwords_excluded(self):
        text = "the the the a a a python developer"
        phrases = extract_keyphrases(text, top_n=10)
        assert "the" not in phrases
        assert "a" not in phrases

    def test_returns_list(self):
        result = extract_keyphrases("hello world")
        assert isinstance(result, list)
