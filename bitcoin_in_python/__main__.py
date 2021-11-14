import argparse
from dataclasses import dataclass
from pprint import pp

from block import BlockChain
from exception import BitcoinException
from storage import unspent_txs_db
from transaction import Transaction
from wallet import Wallet


def main():
    bc = BlockChain.new_block_chain("1DtHd1KgS4c1YrCjuPtEzTtbizsPa47NuR")
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
        parser_send.add_argument("--wallet", required=True)
        parser_send.add_argument("--to", required=True, help="Address of the recipient.")
        parser_send.add_argument("--amount", required=True, type=float)
        parser_send.set_defaults(func=self.send)

        parser_printchain = subparsers.add_parser(
            "printchain", help="Print current blockchain."
        )
        parser_printchain.set_defaults(func=self.print_chain)

        parser_getbalance = subparsers.add_parser(
            "getbalance", help="get balance from an address"
        )
        parser_getbalance.add_argument("--wallet", required=True)
        parser_getbalance.set_defaults(func=self.get_balance)

        parser_createwallet = subparsers.add_parser(
            "createwallet", help="create a new wallet, returns an address"
        )
        parser_createwallet.add_argument("--name", required=True)
        parser_createwallet.set_defaults(func=self.create_wallet)

        args = parser.parse_args()
        if vars(args):
            args.func(args)
        else:
            parser.print_help()

    def send(self, args):
        wallet = Wallet.read_wallet(args.wallet)
        to_wallet = Wallet.read_wallet(args.to)
        tx = Transaction.new_transaction(wallet, to_wallet.get_address(), args.amount, self.bc)
        self.bc.add_block(tx)

    def print_chain(self, args):
        for block in self.bc:
            pp(block)

        print("Unspent transactions set:")
        for tx in unspent_txs_db.values():
            pp(tx)

    def get_balance(self, args):
        wallet = Wallet.read_wallet(args.wallet)
        balance = 0
        for tx in unspent_txs_db.values():
            for output in tx.vout:
                if not output.is_spent and output.can_be_unlocked_with(wallet.get_address()):
                    balance += output.value

        print(f"Balance of {args.wallet}: {balance:.2f}")

    def create_wallet(self, args):
        wallet = Wallet.new_wallet()
        wallet.save_wallet(args.name)
        print(
            f"Your new address is {wallet.get_address()}, "
            f"private key saved to {args.name}.txt"
        )


if __name__ == "__main__":
    try:
        main()
    except BitcoinException as e:
        print("Execution failed with the following error:")
        print(e)
