"""Unit tests for ContentHasher."""

from __future__ import annotations

from app.scraping.scrapers.content_hasher import ContentHasher


class TestHashPage:
    def test_empty_html_returns_consistent_hash(self):
        hasher = ContentHasher()
        result = hasher.hash_page("")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex

    def test_same_html_produces_same_hash(self):
        hasher = ContentHasher()
        html = "<html><body><h1>Software Engineer at Acme</h1></body></html>"
        assert hasher.hash_page(html) == hasher.hash_page(html)

    def test_different_content_produces_different_hash(self):
        hasher = ContentHasher()
        html_a = "<html><body><h1>Job A</h1></body></html>"
        html_b = "<html><body><h1>Job B</h1></body></html>"
        assert hasher.hash_page(html_a) != hasher.hash_page(html_b)

    def test_hash_is_64_char_hex_string(self):
        hasher = ContentHasher()
        result = hasher.hash_page("<p>content</p>")
        assert len(result) == 64
        int(result, 16)  # raises ValueError if not hex

    def test_dynamic_timestamps_stripped_before_hashing(self):
        """Pages with the same content but different timestamps hash identically."""
        hasher = ContentHasher()
        html_old = (
            "<html><body><p>Job listing</p>"
            "<span>Posted 2026-01-01 12:00:00</span></body></html>"
        )
        html_new = (
            "<html><body><p>Job listing</p>"
            "<span>Posted 2026-03-15 09:30:00</span></body></html>"
        )
        assert hasher.hash_page(html_old) == hasher.hash_page(html_new)

    def test_relative_time_stripped(self):
        hasher = ContentHasher()
        html_a = "<p>Job posted 3 days ago</p>"
        html_b = "<p>Job posted 10 hours ago</p>"
        # Both have the same meaningful content after stripping relative time
        # The hashes may differ for other reasons, but the timestamps must be stripped
        cleaned_a = hasher._clean_html(html_a)
        cleaned_b = hasher._clean_html(html_b)
        # Check that neither cleaned version contains the numeric time components
        assert "days ago" not in cleaned_a
        assert "hours ago" not in cleaned_b

    def test_script_tags_removed_before_hashing(self):
        hasher = ContentHasher()
        html_with_script = "<html><script>var nonce='abc'</script><p>Job</p></html>"
        html_without_script = "<html><p>Job</p></html>"
        # Hash should be the same since script is stripped
        assert hasher.hash_page(html_with_script) == hasher.hash_page(html_without_script)

    def test_session_params_stripped(self):
        hasher = ContentHasher()
        html_a = '<a href="/job?id=123&token=abcdef123456">Click</a>'
        html_b = '<a href="/job?id=123&token=fedcba654321">Click</a>'
        cleaned_a = hasher._clean_html(html_a)
        cleaned_b = hasher._clean_html(html_b)
        assert "abcdef123456" not in cleaned_a
        assert "fedcba654321" not in cleaned_b

    def test_whitespace_normalisation(self):
        hasher = ContentHasher()
        html_a = "<p>Content    with  spaces</p>"
        html_b = "<p>Content with spaces</p>"
        # Both should produce the same cleaned text (whitespace is normalised)
        assert hasher.hash_page(html_a) == hasher.hash_page(html_b)

    def test_nonce_hex_strings_stripped(self):
        """Long hex nonces should be stripped from content before hashing."""
        hasher = ContentHasher()
        # Same content but different nonce values → same hash
        html_a = "<p>Job listing abcdef1234567890abcd</p>"
        html_b = "<p>Job listing fedcba0987654321fedc</p>"
        cleaned_a = hasher._clean_html(html_a)
        cleaned_b = hasher._clean_html(html_b)
        # Both nonces should be stripped
        assert "abcdef1234567890abcd" not in cleaned_a
        assert "fedcba0987654321fedc" not in cleaned_b
