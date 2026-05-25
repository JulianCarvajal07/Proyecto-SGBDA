from cryptography.fernet import Fernet
from django.conf import settings

def get_cipher():
    return Fernet(settings.ENCRYPTION_KEY)

def encrypt_password(password: str) -> str:
    """Encripta la contraseña antes de guardarla."""
    cipher = get_cipher()
    return cipher.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Desencripta la contraseña al momento de usarla."""
    cipher = get_cipher()
    return cipher.decrypt(encrypted_password.encode()).decode()