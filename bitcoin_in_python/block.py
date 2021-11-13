import hashlib
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pprint import pprint
from typing import Optional

from exception import BitcoinException
from storage import chain_db, misc_db, unspent_txs_db
from transaction import Transaction, TXOutput

MAX_NONCE = 1 << 64  # 防止 nonce 溢出


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
        chain_db[self.hash] = self

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
        for tx in transactions:
            if not tx.verify():
                raise BitcoinException("Signature verification failed.")

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

    def add_block(self, tx: Transaction):
        coinbase_tx = Transaction.new_coinbase_transaction("admin")
        new_block = Block.new_block([coinbase_tx, tx], self.last_block_hash)
        new_block.insert_to_db()

        # update unspent transactions set
        for tx in new_block.transactions:
            unspent_txs_db[tx.id] = tx

            for input in tx.vin:
                input_tx = unspent_txs_db[input.txid]
                input_tx.vout[input.vout_index].is_spent = True

                all_spent = 1
                for output in input_tx.vout:
                    if not output.is_spent:
                        all_spent = 0
                        break

                if all_spent:
                    unspent_txs_db.pop(input_tx.id)

        self.last_block_hash = new_block.hash
        misc_db['last_block_hash'] = self.last_block_hash

    @classmethod
    def new_block_chain(cls, address: str):
        try:
            last_block_hash = misc_db['last_block_hash']
        except KeyError:
            coinbase_transaction = Transaction.new_coinbase_transaction(address)
            genesis_block = Block.new_genesis_block(coinbase_transaction)
            genesis_block.insert_to_db()
            for tx in genesis_block.transactions:
                unspent_txs_db[tx.id] = tx
            last_block_hash = genesis_block.hash
            misc_db['last_block_hash'] = last_block_hash
        return cls(last_block_hash)

    def __iter__(self):
        """
        从尾到头迭代一条链
        """
        current_block_hash = self.last_block_hash
        try:
            while block := chain_db[current_block_hash]:
                current_block_hash = block.prev_block_hash
                yield block
        except KeyError:
            return

    def find_spendable_transactions(
        self, amount: int, address: str
    ) -> tuple[list[Transaction], int]:
        """
        寻找满足给定金额的最小交易集合.
        """
        accumulated = 0
        rtn = []

        for tx in unspent_txs_db.values():
            should_be_added = 0
            for output in tx.vout:
                if not output.is_spent and output.can_be_unlocked_with(address):
                    accumulated += output.value
                    should_be_added = 1
            if should_be_added:
                rtn.append(tx)

            if accumulated > amount:
                return rtn, accumulated

        raise BitcoinException(f"Not enough funds in address {address}")
