import argparse
from dataclasses import dataclass

from block import BlockChain


def main():
    bc = BlockChain.new_block_chain()
    cli = Cli(bc)
    cli.run()


@dataclass
class Cli:
    bc: BlockChain

    def run(self):
        parser = argparse.ArgumentParser(description='Manage a simple blockchain.', prog='bitcoin_in_python')
        subparsers = parser.add_subparsers()
        parser_addblock = subparsers.add_parser('addblock', help='Add a new block.')
        parser_addblock.set_defaults(func=self.add_block)
        parser_addblock.add_argument('data')
        parser_printchain = subparsers.add_parser('printchain', help='Print current blockchain.')
        parser_printchain.set_defaults(func=self.print_chain)

        args = parser.parse_args()
        args.func(args)

    def add_block(self, args):
        self.bc.add_block(args.data)

    def print_chain(self, args):
        for block in self.bc:
            print(block)


if __name__ == '__main__':
    main()
