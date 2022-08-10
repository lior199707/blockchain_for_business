from funcoin_business.server import Server
import structlog

logger = structlog.getLogger(__name__)


class P2PError(Exception):
    pass


class P2PProtocol:
    """
    class P2PProtocol handles communication on the server, responsible for handling messages on the server.
    """

    def __init__(self, server: Server):
        """
        :param server: Server, the server
        """
        self.server = server
        self.blockchain = server.blockchain
        self.connection_pool = server.connection_pool

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

        await handler(message, writer)
