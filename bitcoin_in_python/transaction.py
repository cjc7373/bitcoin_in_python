import binascii
import random
from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import TYPE_CHECKING

import base58
from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS

from bitcoin_in_python.exception import BitcoinException
from bitcoin_in_python.wallet import Wallet, hex_hash_pubkey

if TYPE_CHECKING:
    from block import BlockChain


@dataclass
class TXOutput:
    value: int  # 交易的货币数量
    pubkey_hash: str
    is_spent: bool = False

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def lock(self, address: str):
        """用收款者地址锁定币."""
        pubkey_hash = base58.b58decode(address).decode()
        pubkey_hash = pubkey_hash[1:-4]
        self.pubkey_hash = pubkey_hash

    def can_be_unlocked_with(self, pubkey_hash: str) -> bool:
        return self.pubkey_hash == pubkey_hash

    def hash(self):
        return sha256(f"{self.value}{self.pubkey_hash}".encode()).hexdigest()


@dataclass
class TXInput:
    txid: str  # 输出的交易
    vout_index: int  # 存储该输出在那笔交易中的索引
    signature: bytes = field(repr=False)
    pubkey: str = field(repr=False)

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def can_unlock_output_with(self, pubkey_hash: str) -> bool:
        locking_hash = hex_hash_pubkey(self.pubkey)
        return locking_hash == pubkey_hash

    def hash(self):
        return sha256(
            f"{self.txid}{self.vout_index}{self.signature}{self.pubkey}".encode()
        ).hexdigest()

    # def __repr__(self):
    #     return f"TXInput: txid={self.txid}, vout_index={self.vout_index} \n"


@dataclass
class Transaction:
    id: str  # 该交易的哈希
    vin: list[TXInput]
    vout: list[TXOutput]

    @classmethod
    def new_coinbase_transaction(cls, to: str):
        """
        奖励矿工的交易, 不需要输出
        """
        SUBSIDY = 1
        out = TXOutput(SUBSIDY, to)

        # 创建一个空的 input 的目的是为了让每次的哈希不同
        input = TXInput("", 0, random.randbytes(20), "")

        tx = cls("", [input], [out])
        tx.hash()
        return tx

    @classmethod
    def new_transaction(cls, wallet: Wallet, to: str, amount: int, bc: "BlockChain"):
        txs, accumulated = bc.find_spendable_transactions(amount, wallet.get_address())

        # build a list of inputs
        inputs = []
        for tx in txs:
            for index, output in enumerate(tx.vout):
                if output.can_be_unlocked_with(wallet.get_address()):
                    inputs.append(
                        TXInput(
                            tx.id,
                            index,
                            b"",
                            wallet.export_public_key(),
                        )
                    )

        outputs = [TXOutput(amount, to)]
        if accumulated > amount:  # 找零
            outputs.append(TXOutput(accumulated - amount, wallet.get_address()))
        tx = cls("", inputs, outputs)
        tx.hash()
        tx.sign(wallet)
        return tx

    def trimmed_copy(self):
        """用于签名的交易副本."""
        inputs = []
        for vin in self.vin:
            inputs.append(TXInput(vin.txid, vin.vout_index, "", ""))
        tx_copy = Transaction(self.id, inputs, self.vout.copy())
        return tx_copy

    @classmethod
    def from_dict(cls, d: dict):
        vin = [TXInput.from_dict(i) for i in d.pop("vin")]
        vout = [TXOutput.from_dict(i) for i in d.pop("vout")]
        return cls(**d, vin=vin, vout=vout)

    def __repr__(self):
        return f"Transaction:\n" f"id={self.id}\n" f"vin={self.vin}\n" f"vout={self.vout}\n"

    def hash(self):
        h = sha256()
        for input in self.vin:
            h.update(input.hash().encode())
        for output in self.vout:
            h.update(output.hash().encode())
        self.id = h.hexdigest()
        return self.id

    def is_coinbase(self):
        return len(self.vin) == 1 and self.vin[0].txid == "" and self.vin[0].pubkey == ""

    def sign(self, wallet: Wallet) -> None:
        if self.is_coinbase():
            return

        signer = DSS.new(wallet.private_key, "fips-186-3")

        tx_copy = self.trimmed_copy()
        for index, vin in enumerate(tx_copy.vin):
            vin.pubkey = wallet.export_public_key()
            tx_copy.id = tx_copy.hash()
            vin.pubkey = ""

            # 由于 signer.sign 方法必须要传一个 Hash 对象, 所以又做了一遍哈希..
            # FIXME: 可以考虑改进
            self.vin[index].signature = signer.sign(SHA256.new(tx_copy.id.encode()))

    def verify(self) -> bool:
        """验证一个 input 的签名"""
        tx_copy = self.trimmed_copy()

        for index, vin in enumerate(tx_copy.vin):
            vin.pubkey = self.vin[index].pubkey
            tx_copy.id = tx_copy.hash()
            vin.pubkey = ""

            pubkey = ECC.import_key(self.vin[index].pubkey)
            verifier = DSS.new(pubkey, "fips-186-3")
            try:
                verifier.verify(
                    # 此处同理, 见 sign 方法
                    SHA256.new(tx_copy.id.encode()),
                    self.vin[index].signature,
                )
            except ValueError:
                return False
        return True
