import argparse
from dataclasses import dataclass

from block import BlockChain
from transaction import Transaction
from exception import BitcoinException


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
        parser_send = subparsers.add_parser("send", help="Send bitcoin to someone.")
        parser_send.add_argument("--from", required=True, dest="_from")
        parser_send.add_argument("--to", required=True)
        parser_send.add_argument("--amount", required=True, type=float)
        parser_send.set_defaults(func=self.send)

        parser_printchain = subparsers.add_parser(
            "printchain", help="Print current blockchain."
        )
        parser_printchain.set_defaults(func=self.print_chain)

        parser_getbalance = subparsers.add_parser(
            "getbalance", help="get balance from an address"
        )
        parser_getbalance.add_argument("--address", required=True)
        parser_getbalance.set_defaults(func=self.get_balance)

        args = parser.parse_args()
        if vars(args):
            args.func(args)
        else:
            parser.print_help()

    def send(self, args):
        try:
            tx = Transaction.new_transaction(args._from, args.to, args.amount, self.bc)
            self.bc.add_block(tx)
        except BitcoinException as e:
            print(e)

    def print_chain(self, args):
        for block in self.bc:
            print(block)

    def get_balance(self, args):
        utxo = self.bc.find_UTXO(args.address)
        balance = 0
        for output_with_transaction in utxo:
            balance += output_with_transaction.output.value

        print(f"Balance of {args.address}: {balance:.2f}")


if __name__ == "__main__":
    main()
