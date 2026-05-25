# utils/fields.py
from django.db import models
from sgbda.utils.encryption import encrypt_password, decrypt_password

class EncryptedPasswordField(models.TextField):
    """Campo que encripta automáticamente al guardar y desencripta al leer."""

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return decrypt_password(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        # Evita doble encriptación si ya está encriptada
        try:
            decrypt_password(value)
            return value  # Ya estaba encriptada
        except Exception:
            return encrypt_password(value)