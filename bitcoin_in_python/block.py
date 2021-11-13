import hashlib
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pprint import pprint
from typing import Optional

from exception import BitcoinException
from storage import db, query, unspent_txs_table
from tinydb.table import Document
from transaction import Transaction, TXOutput

MAX_NONCE = 1 << 64  # 防止 nonce 溢出


@dataclass
class OutputWithTransaction:
    transaction: Transaction
    output: TXOutput
    idx: int


@dataclass
class Block:
    timestamp: int
    transactions: list[Transaction]
    prev_block_hash: str
    nonce: int = 0
    hash: str = ""
    target_bits: int = 8 * 2  # hash 的前缀 0 个数, 即挖矿难度, 需要为 8 的倍数

    def prepare_data(self, nonce) -> str:
        return (
            self.prev_block_hash
            + self.hash_transactions()
            + str(self.timestamp)
            + str(self.target_bits)
            + str(nonce)
        )

    def proof_of_work(self) -> tuple[int, str]:
        target = 1 << (256 - self.target_bits)

        pprint(f"Mining block containing transactions: {self.transactions}")
        start = time.time()
        for nonce in range(MAX_NONCE):
            data = self.prepare_data(nonce).encode()
            h = hashlib.sha256(data)
            hash_int = int.from_bytes(h.digest(), byteorder="big")
            if hash_int < target:
                print(
                    f"Mining done, result hash is {h.hexdigest()}\n"
                    f"Time cost: {time.time() - start:.2f}s\n"
                )
                return nonce, h.hexdigest()
            else:
                continue

        raise BitcoinException("Reached MAX_NONCE, mining aborted.")

    def validate(self) -> bool:
        data = self.prepare_data(self.nonce).encode()
        h = hashlib.sha256(data).digest()
        assert self.target_bits % 8 == 0
        target_bytes = self.target_bits // 8
        if h[:target_bytes] == b"\x00" * target_bytes:
            return True
        else:
            return False

    def to_dict(self):
        block_dict = asdict(self)
        block_dict.update({"type": "block"})
        # pprint(block_dict)
        return block_dict

    def insert_to_db(self):
        db.insert(self.to_dict())

    def hash_transactions(self):
        tx_hashes = ""
        for tx in self.transactions:
            tx_hashes += tx.id
        return hashlib.sha256(tx_hashes.encode()).hexdigest()

    @classmethod
    def from_dict(cls, d: dict):
        d.pop("type", None)
        txs_list = d.pop("transactions")
        txs = [Transaction.from_dict(i) for i in txs_list]
        return cls(**d, transactions=txs)

    @classmethod
    def new_block(cls, transactions: list[Transaction], prev_block_hash: str):
        block = Block(int(datetime.now().timestamp()), transactions, prev_block_hash)

        # 验证每个交易的签名
        # for tx in transactions:
        #     tx.verify()  # FIXME

        block.nonce, block.hash = block.proof_of_work()
        return block

    def __str__(self):
        return (
            f"prev hash: {self.prev_block_hash}\n"
            f"data: {self.transactions}\n"
            f"hash: {self.hash}\n"
            f"POW validation: {'Pass' if self.validate() else 'Failed'}\n"
        )

    @classmethod
    def new_genesis_block(cls, coinbase: Transaction):
        return cls.new_block([coinbase], "0" * 64)


@dataclass
class BlockChain:
    last_block_hash: str
    unspent_txs_set: dict[str, Transaction]  # 更新此项的同时需更新数据库

    def add_block(self, tx: Transaction):
        coinbase_tx = Transaction.new_coinbase_transaction("admin")
        new_block = Block.new_block([coinbase_tx, tx], self.last_block_hash)
        new_block.insert_to_db()

        # update unspent transactions set
        for tx in new_block.transactions:
            self.unspent_txs_set[tx.id] = tx
            unspent_txs_table.insert(Document(asdict(tx), doc_id=tx.id))

            for input in tx.vin:
                input_tx = self.unspent_txs_set[input.txid]
                input_tx.vout[input.vout_index].is_spent = True

                all_spent = 1
                for output in input_tx.vout:
                    if not output.is_spent:
                        all_spent = 0
                        break

                if all_spent:
                    self.unspent_txs_set.pop(input_tx.id)

        self.last_block_hash = new_block.hash
        db.update({"hash": self.last_block_hash}, query.type == "last_block_hash")

    @classmethod
    def new_block_chain(cls, address: str):
        if res := db.search(query.type == "last_block_hash"):
            last_block_hash = res[0]["hash"]
            # TODO: read unspent_txs_set
        else:
            coinbase_transaction = Transaction.new_coinbase_transaction(address)
            genesis_block = Block.new_genesis_block(coinbase_transaction)
            genesis_block.insert_to_db()
            last_block_hash = genesis_block.hash
            db.insert({"type": "last_block_hash", "hash": last_block_hash})
        return cls(last_block_hash, {})

    def __iter__(self):
        """
        从尾到头迭代一条链
        """
        current_block_hash = self.last_block_hash
        while res := db.search(query.fragment({"type": "block", "hash": current_block_hash})):
            current_block_hash = res[0]["prev_block_hash"]
            yield Block.from_dict(res[0])
        return

    def find_UTXO(self, address: str) -> list[OutputWithTransaction]:
        """
        UTXO: Unspent Transactions Outputs
        """
        utxo: list[OutputWithTransaction] = []
        spent_tx_outputs: dict[str, bool] = {}  # key is transaction id + tout index

        for block in self:
            for tx in block.transactions:
                for i in range(len(tx.vout)):
                    if f"{tx.id}{i}" in spent_tx_outputs:
                        continue
                    elif tx.vout[i].can_be_unlocked_with(address):
                        utxo.append(OutputWithTransaction(tx, tx.vout[i], i))

                for input in tx.vin:
                    if input.can_unlock_output_with(address):
                        spent_tx_outputs[f"{input.txid}{input.vout_index}"] = True

        return utxo

    def find_spendable_utxo(
        self, amount: int, address: str
    ) -> tuple[Optional[list[OutputWithTransaction]], int]:
        """
        寻找满足给定金额的最小 UTXO 集合.
        """
        utxo = self.find_UTXO(address)
        accumulated = 0
        rtn = []
        for output_with_transaction in utxo:
            accumulated += output_with_transaction.output.value
            rtn.append(output_with_transaction)
            if accumulated > amount:
                return rtn, accumulated

        return None, 0
