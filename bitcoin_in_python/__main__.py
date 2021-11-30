import argparse
import pickle
from dataclasses import dataclass
from pprint import pp

from bitcoin_in_python.block import BlockChain, blockchain
from bitcoin_in_python.exception import BitcoinException
from bitcoin_in_python.server import (
    Version,
    create_client_socket,
    create_server,
    recv_data,
    send_data,
)
from bitcoin_in_python.storage import unspent_txs_db
from bitcoin_in_python.transaction import Transaction
from bitcoin_in_python.wallet import Wallet


def main():
    try:
        cli = Cli()
        cli.run()
    except BitcoinException as e:
        print("Execution failed with the following error:")
        print(e)


@dataclass
class Cli:
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

        parser_createchain = subparsers.add_parser(
            "createchain", help="Create a new blockchain."
        )
        parser_createchain.add_argument(
            "--wallet", help="The account who creates the genesis block.", required=True
        )
        parser_createchain.set_defaults(func=self.create_chain)

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

        parser_startserver = subparsers.add_parser(
            "startserver", help="Start a server as a mining node."
        )
        parser_startserver.set_defaults(func=self.start_server)

        args = parser.parse_args()
        if vars(args):
            args.func(args)
        else:
            parser.print_help()

    def send(self, args):
        wallet = Wallet.read_wallet(args.wallet)
        to_wallet = Wallet.read_wallet(args.to)
        tx = Transaction.new_transaction(wallet, to_wallet.get_address(), args.amount, self.bc)
        BlockChain().add_block(tx)

    def print_chain(self, args):
        with create_client_socket(4000) as s:
            version = Version(len(blockchain), "")  # FIXME
            send_data('pull chain', pickle.dumps(version), s)
            _, data = recv_data(s)
            data = pickle.loads(data)
            print(data)

        for block in BlockChain():
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

    def create_chain(self, args):
        wallet = Wallet.read_wallet(args.wallet)
        BlockChain.new_block_chain(wallet.get_address())

    def start_server(self, args):
        create_server(4000)


if __name__ == "__main__":
    main()
