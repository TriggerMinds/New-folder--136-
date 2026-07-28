from app.services.content_hashing import sha256_text


def test_sha256_text_consistency():
    result1 = sha256_text("hello world")
    result2 = sha256_text("hello world")
    assert result1 == result2


def test_sha256_text_length():
    result = sha256_text("test content")
    assert len(result) == 64


def test_sha256_text_hex_chars():
    result = sha256_text("test")
    assert all(c in "0123456789abcdef" for c in result)


def test_sha256_text_different_inputs():
    r1 = sha256_text("content A")
    r2 = sha256_text("content B")
    assert r1 != r2


def test_sha256_text_empty_string():
    result = sha256_text("")
    assert len(result) == 64
