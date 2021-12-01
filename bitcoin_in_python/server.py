import pickle
import socket
from dataclasses import dataclass

from bitcoin_in_python.block import blockchain
from bitcoin_in_python.transaction import Transaction
from bitcoin_in_python.wallet import Wallet


@dataclass
class Version:
    height: int
    address_from: str


def send_data(command: str, data: bytes, conn: socket.socket) -> None:
    assert len(command) <= 12
    length = len(data)
    data = length.to_bytes(4, byteorder='big') + command.ljust(12).encode() + data
    conn.sendall(data)


def recv_data(conn: socket.socket) -> tuple[str, bytes]:
    metadata = conn.recv(16)
    length = int.from_bytes(metadata[:4], byteorder='big')
    command = metadata[4:].decode().strip()  # may contain padding
    received = 0
    data = b''
    while received < length:
        data += conn.recv(4096)
        received += len(data)
    return command, data


pending_transactions = []


def command_handler(command: str, data: bytes, conn: socket.socket, wallet: Wallet):
    print(f"Received command {command}")
    if command == 'pull chain':
        # Receiving Version object
        version = pickle.loads(data)
        if len(blockchain) > version.height:
            blocks = blockchain.top_n_blocks(len(blockchain) - version.height)
            print(f"Sending {len(blocks)} block(s)")
            send_data('reply', pickle.dumps(blocks), conn)
    if command == 'send':
        global pending_transactions
        # Receiving a list of transactions
        txs: list[Transaction] = pickle.loads(data)
        print(f"Receiving {len(txs)} transaction(s).")
        pending_transactions += txs
        if len(pending_transactions) >= 2:
            print("Mining a new block..")
            block = blockchain.create_block(pending_transactions, wallet.get_address())
            pending_transactions.clear()

            # Return the new block
            print(f"Sending a new block..")
            send_data('reply', pickle.dumps(block), conn)
        else:
            print("Only one pending transaction, waiting for another..")
            send_data('empty', b'', conn)


def create_client_socket(port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', port))
    return s


def create_server(port: int, wallet: Wallet):
    """
    自定义一种协议, 前 4 字节为长度, 接 12 字节为命令名称, 接下来为数据.
    每个 socket 在通信一次后即关闭 (和 HTTP 类似)
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', port))
        print(f"Starting node at localhost:{port}")
        s.listen(5)
        while True:
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                command, data = recv_data(conn)
                command_handler(command, data, conn, wallet)
