from dataclasses import dataclass
from datetime import datetime
import hashlib
from typing import Optional
import time

MAX_NONCE = 1 << 64  # 防止 nonce 溢出


@dataclass
class Block:
    timestamp: datetime
    data: str
    prev_block_hash: str
    nonce: int = 0
    hash: str = ''
    target_bits: int = 8 * 2  # hash 的前缀 0 个数, 即挖矿难度, 需要为 8 的倍数

    def prepare_data(self, nonce) -> str:
        return self.prev_block_hash + \
                    self.data + \
                    str(int(self.timestamp.timestamp())) + \
                    str(self.target_bits) + \
                    str(nonce)

    def proof_of_work(self) -> Optional[tuple[int, str]]:
        target = 1 << (256 - self.target_bits)

        print(f"Mining block containing data: {self.data}")
        start = time.time()
        for nonce in range(MAX_NONCE):
            data = self.prepare_data(nonce).encode()
            h = hashlib.sha256(data)
            hash_int = int.from_bytes(h.digest(), byteorder='big')
            if hash_int < target:
                print(f"Mining done, result hash is {h.hexdigest()}\n"
                      f"Time cost: {time.time() - start:.2f}s\n")
                return nonce, h.hexdigest()
            else:
                continue

        return None

    def validate(self) -> bool:
        data = self.prepare_data(self.nonce).encode()
        h = hashlib.sha256(data).digest()
        assert self.target_bits % 8 == 0
        target_bytes = self.target_bits // 8
        if h[:target_bytes] == b'\x00' * target_bytes:
            return True
        else:
            return False

    @classmethod
    def new_block(cls, data: str, prev_block_hash: str):
        block = Block(datetime.now(), data, prev_block_hash)
        block.nonce, block.hash = block.proof_of_work()
        return block

    def __str__(self):
        return f"prev hash: {self.prev_block_hash}\n" \
               f"data: {self.data}\n" \
               f"hash: {self.hash}\n" \
               f"POW validation: {'Pass' if self.validate() else 'Failed'}\n"

    @classmethod
    def new_genesis_block(cls):
        return cls.new_block("Genesis Block", '')


@dataclass
class BlockChain:
    blocks: list[Block]

    def add_block(self, data: str):
        prev_block = self.blocks[-1]
        new_block = Block.new_block(data, prev_block.hash)
        self.blocks.append(new_block)

    @classmethod
    def new_block_chain(cls):
        return cls([Block.new_genesis_block()])
