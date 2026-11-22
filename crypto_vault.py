"""Token storage, PBKDF2 key derivation, AES-GCM envelopes and replay checks."""
import base64, json, os, time
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import keyring
from config import PBKDF2_ITERATIONS
SERVICE, USERNAME = "mdotk-mote", "remote-token"
def save_token(token: str) -> None: keyring.set_password(SERVICE, USERNAME, token)
def load_token() -> str | None: return keyring.get_password(SERVICE, USERNAME)
def delete_token() -> None:
    try: keyring.delete_password(SERVICE, USERNAME)
    except keyring.errors.PasswordDeleteError: pass
def derive_key(token: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=iterations)
    return kdf.derive(token.encode())
def encrypt_envelope(key: bytes, seq: int, payload: dict) -> dict:
    ts, nonce = int(time.time()), os.urandom(12)
    aad = f"{seq}:{ts}".encode()
    cipher = AESGCM(key).encrypt(nonce, json.dumps(payload, separators=(",", ":")).encode(), aad)
    return {"seq":seq,"ts":ts,"nonce":base64.b64encode(nonce).decode(),"data":base64.b64encode(cipher).decode()}
def decrypt_envelope(key: bytes, envelope: dict, expected_seq: int, max_skew: int = 90) -> dict:
    seq, ts = int(envelope["seq"]), int(envelope["ts"])
    if seq != expected_seq: raise ValueError("sequence mismatch")
    if abs(int(time.time())-ts)>max_skew: raise ValueError("timestamp expired")
    nonce=base64.b64decode(envelope["nonce"], validate=True); ciphertext=base64.b64decode(envelope["data"], validate=True)
    return json.loads(AESGCM(key).decrypt(nonce,ciphertext,f"{seq}:{ts}".encode()).decode())
