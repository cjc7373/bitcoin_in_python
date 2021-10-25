from dataclasses import dataclass
from datetime import datetime
import hashlib
import binascii
from typing import Optional
import time

MAX_NONCE = 1 << 64  # 防止 nonce 溢出


@dataclass
class Block:
    timestamp: datetime
    data: bytes
    prev_block_hash: bytes
    nonce: int = 0
    hash: bytes = b''
    target_bits: int = 8 * 2  # hash 的前缀 0 个数, 即挖矿难度, 需要为 8 的倍数

    def prepare_data(self, nonce) -> bytes:
        return self.prev_block_hash + \
                    self.data + \
                    int(self.timestamp.timestamp()).to_bytes(10, byteorder='big') + \
                    self.target_bits.to_bytes(8, byteorder='big') + \
                    nonce.to_bytes(8, byteorder='big')

    def proof_of_work(self) -> Optional[tuple[int, bytes]]:
        target = 1 << (256 - self.target_bits)

        print(f"Mining block containing data: {self.data.decode()}")
        start = time.time()
        for nonce in range(MAX_NONCE):
            data = self.prepare_data(nonce)
            h = hashlib.sha256(data).digest()
            hash_int = int.from_bytes(h, byteorder='big')
            if hash_int < target:
                print(f"Mining done, result hash is {binascii.hexlify(h)}\n"
                      f"Time cost: {time.time() - start:.2f}s\n")
                return nonce, h
            else:
                continue

        return None

    def validate(self) -> bool:
        data = self.prepare_data(self.nonce)
        h = hashlib.sha256(data).digest()
        assert self.target_bits % 8 == 0
        target_bytes = self.target_bits // 8
        if h[:target_bytes] == b'\x00' * target_bytes:
            return True
        else:
            return False

    @classmethod
    def new_block(cls, data: str, prev_block_hash: bytes):
        block = Block(datetime.now(), data.encode(), prev_block_hash)
        block.nonce, block.hash = block.proof_of_work()
        return block

    def __str__(self):
        return f"prev hash: {binascii.hexlify(self.prev_block_hash)}\n" \
               f"data: {self.data.decode()}\n" \
               f"hash: {binascii.hexlify(self.hash)}\n" \
               f"POW validation: {'Pass' if self.validate() else 'Failed'}\n"

    @classmethod
    def new_genesis_block(cls):
        return cls.new_block("Genesis Block", b'')


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
