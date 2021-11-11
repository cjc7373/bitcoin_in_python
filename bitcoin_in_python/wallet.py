from dataclasses import dataclass
from hashlib import sha256
import binascii

from Crypto.PublicKey import ECC
from Crypto.Hash import RIPEMD160
import base58

from storage import save_str_to_file, read_str_from_file


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

    def save_wallet(self, name):
        save_str_to_file(self.private_key, f"{name}.txt")

    @classmethod
    def read_wallet(cls, name):
        key_str = read_str_from_file(f"{name}.txt")
        key = ECC.import_key(key_str)
        pub_str = key.public_key().export_key(format="PEM")
        return cls(key_str, pub_str)

    def get_address(self) -> str:
        hsh = hash_pubkey(self.public_key)

        prefix = b"\x00"  # P2PKH address

        checksum = sha256(sha256(prefix + hsh).digest()).digest()[:4]

        address = base58.b58encode(prefix + hsh + checksum).decode()
        return address


@dataclass
class Wallets:
    wallets: dict[str, Wallet]
