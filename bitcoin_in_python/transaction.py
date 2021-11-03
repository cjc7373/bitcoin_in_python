from dataclasses import dataclass, asdict
from typing import TYPE_CHECKING
from hashlib import sha256

from exception import BitcoinException

if TYPE_CHECKING:
    from block import BlockChain


@dataclass
class TXOutput:
    value: int  # 交易的货币数量
    script_pub_key: str

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def can_be_unlocked_with(self, unlocking_data: str) -> bool:
        return self.script_pub_key == unlocking_data

    def hash(self):
        return sha256(f"{self.value}{self.script_pub_key}".encode()).hexdigest()


@dataclass
class TXInput:
    txid: str  # 输出的交易
    vout_index: int  # 存储该输出在那笔交易中的索引
    script_sig: str

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def can_unlock_output_with(self, unlocking_data: str) -> bool:
        return self.script_sig == unlocking_data

    def hash(self):
        return sha256(
            f"{self.txid}{self.vout_index}{self.script_sig}".encode()
        ).hexdigest()


@dataclass
class Transaction:
    id: str  # 该交易的哈希
    vin: list[TXInput]
    vout: list[TXOutput]

    @classmethod
    def new_coinbase_transaction(cls, to: str, data: str = None):
        """
        奖励矿工的交易, 不需要输出
        """
        subsidy = 1

        if not data:
            data = f"Reward to {to}"

        txin = TXInput("", -1, data)
        txout = TXOutput(subsidy, to)
        tx = cls("", [txin], [txout])
        tx.hash()
        return tx

    @classmethod
    def new_transaction(cls, _from: str, to: str, amount: int, bc: "BlockChain"):
        utxo, accumulated = bc.find_spendable_utxo(amount, _from)
        if utxo:
            # build a list of inputs
            inputs = []
            for output_with_transaction in utxo:
                inputs.append(
                    TXInput(
                        output_with_transaction.transaction.id,
                        output_with_transaction.index,
                        _from,
                    )
                )

            outputs = [TXOutput(amount, to)]
            if accumulated > amount:  # 找零
                outputs.append(TXOutput(accumulated - amount, _from))
            tx = cls("", inputs, outputs)
            tx.hash()
            return tx
        else:
            raise BitcoinException("Not enough funds.")

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
