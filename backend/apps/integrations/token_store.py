from django.core import signing

TOKEN_SALT = "instagram-access-token"


def encrypt_token(token: str) -> str:
    return signing.dumps(token, salt=TOKEN_SALT)


def decrypt_token(encrypted: str) -> str:
    return signing.loads(encrypted, salt=TOKEN_SALT)
