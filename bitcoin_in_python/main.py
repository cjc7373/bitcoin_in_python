from block import BlockChain
from tinydb import TinyDB, Query

db = TinyDB('../db.json')


def main():
    bc = BlockChain.new_block_chain()
    bc.add_block("Send 1 BTC to Ivan")
    bc.add_block("Send 2 more BTC to Ivan")

    for block in bc.blocks:
        db.insert({'type': 'data', 'data': block.data.decode()})
        print(block)


if __name__ == '__main__':
    main()
