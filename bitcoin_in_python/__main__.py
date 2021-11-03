import argparse
from dataclasses import dataclass

from block import BlockChain


def main():
    bc = BlockChain.new_block_chain("admin")
    cli = Cli(bc)
    cli.run()


@dataclass
class Cli:
    bc: BlockChain

    def run(self):
        parser = argparse.ArgumentParser(
            description="Manage a simple blockchain.", prog="bitcoin_in_python"
        )
        subparsers = parser.add_subparsers()
        parser_addblock = subparsers.add_parser("addblock", help="Add a new block.")
        parser_addblock.add_argument("data")
        parser_addblock.add_argument("--address")
        parser_addblock.set_defaults(func=self.add_block)

        parser_printchain = subparsers.add_parser(
            "printchain", help="Print current blockchain."
        )
        parser_printchain.set_defaults(func=self.print_chain)

        parser_getbalance = subparsers.add_parser(
            "getbalance", help="get balance from an address"
        )

        args = parser.parse_args()
        if vars(args):
            args.func(args)
        else:
            parser.print_help()

    def add_block(self, args):
        self.bc.add_block(args.data)

    def print_chain(self, args):
        for block in self.bc:
            print(block)


if __name__ == "__main__":
    main()
