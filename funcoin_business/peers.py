from funcoin_business.connections import ConnectionPool
import structlog

logger = structlog.getLogger(__name__)


class P2PError(Exception):
    pass


class P2PProtocol:
    """
    class P2PProtocol handles communication on the server, responsible for handling messages on the server.
    """

    def __init__(self, connection_pool: ConnectionPool):
        """
        :param connection_pool: ConnectionPool, the pool of all connected users
        """
        self.connection_pool = connection_pool

    async def handle_message(self, message: dict):
        """
        responsible for identifying the action according to the message name and calling the proper action
        if the name of the action is not valid raising P2PError(Exception).

        :raise: P2PError
        :param message: message object, dict {name: ...,payload: ... }
        TransactionMessage, PeerMessage, BlockMessage
        """
        message_handlers = {
            "block": self.handle_block,
            "peer": self.handle_peer,
            "transaction": self.handle_transaction,
        }

        handler = message_handlers.get(message["name"])
        if not handler:
            raise P2PError("Missing handler for message")

        msg = await handler(message["payload"])
        await self.connection_pool.broadcast(msg)

    async def handle_peer(self, peer_payload: dict) -> str:
        """
        Handles a peer message

        :param peer_payload: schema.PeerSchema
        :return: str, the message to broadcast to all connected users about a new peer joining
        """
        address = peer_payload["address"]
        msg = f"New user [ip: {address['ip']}, port: {address['port']}, last_Seen: {peer_payload['last_seen']}]" \
              f"\r\nis now authorized"
        return msg

    async def handle_block(self, block_payload: dict):
        """
        Handles a block message

        :param block_payload: schema.BlockSchema
        :return: str, the message to broadcast to all connected users about a new block that was created
        """
        pass

    async def handle_transaction(self, transaction_payload: dict) -> str:
        """
        Handles a transaction message

        :param transaction_payload: schema.TransactionSchema
        :return: str, the message to broadcast to all connected users about a transaction was made
        """
        car = transaction_payload["item"]
        msg = "New Transaction:\r\n"
        msg += f"The time of the transaction: {transaction_payload['timestamp']}\r\n"
        msg += f"The sender: {transaction_payload['sender']}\r\n"
        msg += f"The receiver: {transaction_payload['receiver']}, {car['owner']['access']}\r\n"
        msg += f"The car:\r\n"
        msg += f"  id: {car['id']}\r\n"
        msg += f"  model: {car['model']}\r\n"
        msg += f"  color: {car['color']}"
        return msg
