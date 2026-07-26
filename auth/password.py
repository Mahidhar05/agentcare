# auth/password.py

from passlib.context import CryptContext

# ── Password hashing context using bcrypt ─────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hashes a plain text password using bcrypt.
    Returns the hashed string to store in the database.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against a bcrypt hash.
    Returns True if match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)