from pipeline.hashing import content_hash, hash_id


def test_hash_is_deterministic_for_same_salt():
    assert hash_id("author-42", "salt") == hash_id("author-42", "salt")


def test_hash_changes_with_salt():
    assert hash_id("author-42", "salt-a") != hash_id("author-42", "salt-b")


def test_hash_is_not_the_plaintext():
    h = hash_id("author-42", "salt")
    assert h is not None
    assert "author-42" not in h
    assert len(h) == 16
    int(h, 16)  # valid hex


def test_blank_and_none_map_to_none():
    assert hash_id(None, "salt") is None
    assert hash_id("", "salt") is None
    assert hash_id("   ", "salt") is None


def test_content_hash_is_stable_and_order_sensitive():
    assert content_hash("a", "b") == content_hash("a", "b")
    assert content_hash("a", "b") != content_hash("b", "a")
