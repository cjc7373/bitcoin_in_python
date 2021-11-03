from dataclasses import dataclass, asdict


@dataclass
class TXOutput:
    value: int  # 交易的货币数量
    script_pub_key: str

    @classmethod
    def from_dict(cls, d: dict):
        return cls(**d)

    def can_be_unlocked_with(self, unlocking_data: str) -> bool:
        return self.script_pub_key == unlocking_data


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


@dataclass
class Transaction:
    id: str  # TODO: 这是什么?
    vin: list[TXInput]
    vout: list[TXOutput]

    @classmethod
    def new_coinbase_transaction(cls, to, data: str):
        """
        奖励矿工的交易, 不需要输出
        """
        subsidy = 1

        if not data:
            data = f"Reward to {to}"

        txin = TXInput("", -1, data)
        txout = TXOutput(subsidy, to)
        tx = cls("", [txin], [txout])
        return tx

    @classmethod
    def from_dict(cls, d: dict):
        vin = [TXInput.from_dict(i) for i in d.pop("vin")]
        vout = [TXOutput.from_dict(i) for i in d.pop("vout")]
        return cls(**d, vin=vin, vout=vout)

    def __str__(self):
        return str(asdict(self))
