import binascii
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import TYPE_CHECKING

import base58
from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import DSS
from exception import BitcoinException
from wallet import Wallet, hex_hash_pubkey

if TYPE_CHECKING:
    from block import BlockChain, OutputWithTransaction


@dataclass
class TXOutput:
    value: int  # 交易的货币数量
    pubkey_hash: str

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
    signature: str
    pubkey: str

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
        tx = cls("", [], [out])
        tx.hash()
        return tx

    @classmethod
    def new_transaction(cls, wallet: Wallet, to: str, amount: int, bc: "BlockChain"):
        utxo, accumulated = bc.find_spendable_utxo(amount, wallet.get_address())
        if utxo:
            # build a list of inputs
            inputs = []
            for output_with_transaction in utxo:
                inputs.append(
                    TXInput(
                        output_with_transaction.transaction.id,
                        output_with_transaction.idx,
                        "",
                        wallet.public_key,
                    )
                )

            outputs = [TXOutput(amount, to)]
            if accumulated > amount:  # 找零
                outputs.append(TXOutput(accumulated - amount, wallet.get_address()))
            tx = cls("", inputs, outputs)
            tx.hash()
            tx.sign(utxo, wallet.private_key)
            return tx
        else:
            raise BitcoinException("Not enough funds.")

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

    def __str__(self):
        return str(asdict(self))

    def hash(self):
        h = sha256()
        for input in self.vin:
            h.update(input.hash().encode())
        for output in self.vout:
            h.update(output.hash().encode())
        self.id = h.hexdigest()
        return self.id

    def is_coinbase(self):
        return len(self.vin) == 0

    def sign(self, utxo: list["OutputWithTransaction"], private_key: str) -> None:
        if self.is_coinbase():
            return

        key = ECC.import_key(private_key)
        signer = DSS.new(key, "fips-186-3")

        tx_copy = self.trimmed_copy()
        for index, vin in enumerate(tx_copy.vin):
            vin.pubkey = utxo[index].output.pubkey_hash
            tx_copy.id = tx_copy.hash()
            vin.pubkey = ""

            # 由于 signer.sign 方法必须要传一个 Hash 对象, 所以又做了一遍哈希..
            sig_bytes = signer.sign(SHA256.new(tx_copy.id.encode()))
            self.vin[index].signature = binascii.hexlify(sig_bytes).decode()

    def verify(self, utxo: list["OutputWithTransaction"]) -> bool:
        """验证一个 input 的签名"""
        tx_copy = self.trimmed_copy()

        for index, vin in enumerate(tx_copy.vin):
            vin.pubkey = utxo[index].output.pubkey_hash
            tx_copy.id = tx_copy.hash()
            vin.pubkey = ""

            pubkey = ECC.import_key(self.vin[index].pubkey)
            verifier = DSS.new(pubkey, "fips-186-3")
            try:
                verifier.verify(
                    # 此处同理, 见 sign 方法
                    SHA256.new(tx_copy.id.encode()),
                    binascii.unhexlify(self.vin[index].signature),
                )
            except ValueError:
                return False
        return True
