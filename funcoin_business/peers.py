import asyncio

import structlog

import funcoin_business.server

logger = structlog.getLogger(__name__)


class P2PError(Exception):
    pass


class P2PProtocol:
    """
    class P2PProtocol handles communication on the server, responsible for handling messages on the server.
    """

    def __init__(self, server: funcoin_business.server.Server):
        self.server = server
        self.blockchain = server.blockchain
        self.connection_pool = server.connection_pool

    async def handle_message(self, message, writer):
        """
        responsible for identifying the action according to the message name and calling the proper action
        if the name of the action is not valid raising P2PError(Exception).

        :param message: message object, dict {name: ...,payload: ... }
        :param writer: asyncio.StreamWriter object, the user
        """
        message_handlers = {
            "block": self.handle_block,
            "ping": self.handle_ping,
            "peers": self.handle_peers,
            "transactions": self.handle_transaction,
        }

        handler = message_handlers.get(message["name"])
        if not handler:
            raise P2PError("Missing handler for message")

        await handler(message, writer)
