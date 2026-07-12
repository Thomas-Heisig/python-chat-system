import hashlib
import hmac
import os

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 120000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False

    # Legacy compatibility: allow plain-text and plain sha256 hashes from older local datasets.
    if "$" not in password_hash:
        if hmac.compare_digest(password_hash, password):
            return True
        legacy_sha256 = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(password_hash, legacy_sha256)

    try:
        algorithm, iterations_raw, salt_hex, expected_hex = password_hash.split("$", 3)
        if not algorithm.startswith("pbkdf2_"):
            return False
        digest_name = algorithm.replace("pbkdf2_", "", 1)
        iterations = int(iterations_raw)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except (TypeError, ValueError):
        return False

    actual = hashlib.pbkdf2_hmac(digest_name, password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)
