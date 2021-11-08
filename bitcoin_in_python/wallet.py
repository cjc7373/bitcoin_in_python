from dataclasses import dataclass
from hashlib import sha256
import binascii

from Crypto.PublicKey import ECC
from Crypto.Hash import RIPEMD160
import base58


def new_key_pair() -> (str, str):
    key = ECC.generate(curve="p256")
    pub = key.public_key()
    return key.export_key(format="PEM"), pub.export_key(format="PEM")


def hash_pubkey(pub: str) -> bytes:
    pub = ECC.import_key(pub)
    hsh: bytes = sha256(pub.export_key(format="DER")).digest()
    hsh = RIPEMD160.new(hsh).digest()
    return hsh


def hex_hash_pubkey(pub: str) -> str:
    return binascii.hexlify(hash_pubkey(pub)).decode()


@dataclass
class Wallet:
    private_key: str
    public_key: str

    @classmethod
    def new_wallet(cls):
        key, pub = new_key_pair()
        return cls(key, pub)

    def get_address(self) -> str:
        hsh = hash_pubkey(self.public_key)

        prefix = b"\x00"  # P2PKH address

        checksum = sha256(sha256(prefix + hsh).digest()).digest()[:4]

        address = base58.b58encode(prefix + hsh + checksum).decode()
        return address


@dataclass
class Wallets:
    wallets: dict[str, Wallet]
