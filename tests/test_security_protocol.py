"""Portable protocol/security regression tests; no desktop peripherals required."""
import sys, types, unittest
# Keyring is optional on CI; inject a deterministic test-only backend shim.
if 'keyring' not in sys.modules:
    kr = types.ModuleType('keyring')
    kr.errors = types.SimpleNamespace(PasswordDeleteError=Exception)
    kr.set_password = lambda *args: None
    kr.get_password = lambda *args: None
    kr.delete_password = lambda *args: None
    sys.modules['keyring'] = kr

from crypto_vault import derive_key, encrypt_envelope, decrypt_envelope

class CryptoProtocolTests(unittest.TestCase):
    def setUp(self):
        self.key = derive_key('correct horse battery staple', b'0123456789abcdef', 1000)
    def test_round_trip(self):
        envelope = encrypt_envelope(self.key, 1, {'kind':'media','action':'play_pause','data':{}})
        self.assertEqual(decrypt_envelope(self.key, envelope, 1), {'kind':'media','action':'play_pause','data':{}})
    def test_replay_sequence_rejected(self):
        envelope = encrypt_envelope(self.key, 4, {'kind':'media'})
        with self.assertRaises(ValueError):
            decrypt_envelope(self.key, envelope, 5)
    def test_ciphertext_tampering_rejected(self):
        envelope = encrypt_envelope(self.key, 1, {'kind':'media'})
        envelope['data'] = envelope['data'][:-4] + 'AAAA'
        with self.assertRaises(Exception):
            decrypt_envelope(self.key, envelope, 1)
    def test_wrong_token_derives_different_key(self):
        other = derive_key('wrong token', b'0123456789abcdef', 1000)
        self.assertNotEqual(self.key, other)

if __name__ == '__main__': unittest.main()
