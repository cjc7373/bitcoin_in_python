from dataclasses import dataclass


@dataclass
class TXOutput:
    value: int
    script_pub_key: str


@dataclass
class TXInput:
    txid: str
    vout: int
    script_sig: str


@dataclass
class Transaction:
    id: str
    vin: TXInput
    vout: TXOutput
