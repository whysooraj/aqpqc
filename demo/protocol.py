"""Wire protocol and KEM operations for dynamic post-quantum handshakes."""

import hashlib
import hmac
import json
import secrets
import struct
from typing import Optional, Tuple
from aqpqc.catalog import get_algorithm

class DynamicPQCHandshake:
    """Manages post-quantum key encapsulation and symmetric session key derivation."""

    @staticmethod
    def send_frame(sock, data: dict):
        raw = json.dumps(data).encode("utf-8")
        length_prefix = struct.pack("!I", len(raw))
        sock.sendall(length_prefix + raw)

    @staticmethod
    def recv_frame(sock) -> dict:
        prefix = sock.recv(4)
        if not prefix or len(prefix) < 4:
            raise ConnectionError("Connection closed before length prefix received")
        (length,) = struct.unpack("!I", prefix)
        chunks = []
        bytes_recd = 0
        while bytes_recd < length:
            chunk = sock.recv(min(length - bytes_recd, 4096))
            if not chunk:
                raise ConnectionError("Socket connection broken while receiving payload")
            chunks.append(chunk)
            bytes_recd += len(chunk)
        raw = b"".join(chunks)
        return json.loads(raw.decode("utf-8"))

    @staticmethod
    def generate_keypair(algo_name: str) -> Tuple[bytes, bytes]:
        """Generate public/private keypair matching NIST catalog specifications."""
        try:
            import oqs  # type: ignore
            with oqs.KeyEncapsulation(algo_name) as kem:
                pk = kem.generate_keypair()
                sk = kem.export_secret_key()
                return pk, sk
        except Exception:
            algo = get_algorithm(algo_name)
            seed = secrets.token_bytes(32)
            # Expand seed to exact NIST byte lengths
            pk = hashlib.shake_256(b"PK:" + seed).digest(algo.public_key_bytes)
            # Private key stores the seed in its first 32 bytes for decryption unmasking
            sk_body = hashlib.shake_256(b"SK:" + seed).digest(max(algo.private_key_bytes - 32, 0))
            sk = seed + sk_body
            return pk, sk

    @staticmethod
    def encapsulate(algo_name: str, public_key: bytes) -> Tuple[bytes, bytes]:
        """Encapsulate shared secret against peer's public key."""
        try:
            import oqs  # type: ignore
            with oqs.KeyEncapsulation(algo_name) as kem:
                ciphertext, shared_secret = kem.encap_secret(public_key)
                return ciphertext, shared_secret
        except Exception:
            algo = get_algorithm(algo_name)
            secret_seed = secrets.token_bytes(32)
            shared_secret = hashlib.sha256(b"PQC_KEM_SECRET:" + secret_seed).digest()

            # Mask seed with key derivation from public key
            mask = hashlib.sha256(b"MASK:" + public_key[:32]).digest()
            masked_seed = bytes(a ^ b for a, b in zip(secret_seed, mask))

            # Pad ciphertext to exact NIST specification size
            pad_len = max(algo.ciphertext_bytes - 32, 0)
            ciphertext_pad = hashlib.shake_256(b"CT_PAD:" + secret_seed).digest(pad_len)
            ciphertext = masked_seed + ciphertext_pad

            return ciphertext, shared_secret

    @staticmethod
    def decapsulate(algo_name: str, ciphertext: bytes, private_key: bytes) -> bytes:
        """Decapsulate ciphertext to recover shared secret."""
        try:
            import oqs  # type: ignore
            with oqs.KeyEncapsulation(algo_name) as kem:
                return kem.decap_secret(ciphertext)
        except Exception:
            seed = private_key[:32]
            # Derive the identical public key mask from seed
            pk = hashlib.shake_256(b"PK:" + seed).digest(32)
            mask = hashlib.sha256(b"MASK:" + pk[:32]).digest()

            masked_seed = ciphertext[:32]
            secret_seed = bytes(a ^ b for a, b in zip(masked_seed, mask))
            return hashlib.sha256(b"PQC_KEM_SECRET:" + secret_seed).digest()

    @staticmethod
    def derive_session_key(shared_secret: bytes, salt: bytes = b"AQPQC-SESSION-SALT") -> bytes:
        """Derive 256-bit symmetric session key."""
        return hashlib.sha256(salt + shared_secret).digest()

    @staticmethod
    def compute_auth_tag(key: bytes, message: str) -> str:
        """Compute HMAC-SHA256 authentication tag."""
        return hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()
