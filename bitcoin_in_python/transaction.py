from dataclasses import dataclass


@dataclass
class TXOutput:
    value: int
    script_pub_key: str


@dataclass
class TXInput:
    txid: str
    vout: int  # 存储该输出在那笔交易中的索引
    script_sig: str


@dataclass
class Transaction:
    id: str
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
