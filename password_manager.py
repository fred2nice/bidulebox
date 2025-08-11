import os
import aesio
from binascii import hexlify, unhexlify

class PasswordManager:
    def __init__(self, aes_key):
        self.aes_key = aes_key
        if len(self.aes_key) not in [16, 24, 32]:
            raise ValueError("La clé doit comporter 16, 24 ou 32 octets")
        self.keys_dir = "/.keys"
        self._create_keys_dir()

    def _create_keys_dir(self):
        try:
            os.mkdir(self.keys_dir)
        except OSError:
            pass  # Le dossier existe déjà

    def _pad_password(self, password):
        """
        Ajoute des espaces à la fin du mot de passe pour garantir une longueur multiple de 16.
        """
        padding_length = 16 - (len(password) % 16)
        return password + ' ' * padding_length

    def _encrypt_password(self, password):
        cipher = aesio.AES(self.aes_key, aesio.MODE_ECB)
        password_padded = self._pad_password(password)  # Padding du mot de passe
        encrypted = bytearray(len(password_padded))
        cipher.encrypt_into(password_padded.encode('utf-8'), encrypted)
        return hexlify(encrypted).decode('utf-8')

    def _decrypt_password(self, encrypted_password):
        cipher = aesio.AES(self.aes_key, aesio.MODE_ECB)
        encrypted_bytes = unhexlify(encrypted_password)
        decrypted = bytearray(len(encrypted_bytes))
        cipher.decrypt_into(encrypted_bytes, decrypted)
        return decrypted.decode('utf-8').rstrip()  # Supprime les espaces ajoutés lors du padding

    def store_password(self, service_name, password):
        encrypted_password = self._encrypt_password(password)
        with open(f"{self.keys_dir}/{service_name}.key", "w",encoding='utf-8') as key_file:
            key_file.write(encrypted_password)

    def load_password(self, service_name):
        try:
            with open(f"{self.keys_dir}/{service_name}.key", "r",encoding='utf-8') as key_file:
                encrypted_password = key_file.read()
                return self._decrypt_password(encrypted_password)
        except OSError:
            return None

    def delete_password(self, service_name):
        try:
            os.remove(f"{self.keys_dir}/{service_name}.key")
        except OSError:
            pass  # Gérer l'erreur si le fichier n'existe pas


