import json
from textwrap import dedent

from marshmallow.exceptions import MarshmallowError

from funcoin_business.connections import ConnectionPool
from funcoin_business.blockchain import Blockchain
import asyncio
import structlog
from funcoin_business.utils import get_fake_ip_and_port, get_external_ip
from funcoin_business.schema import AddressSchema
from funcoin_business.users.user import User
from funcoin_business.users.authorized_user import AuthorizedUser
from funcoin_business.messages import create_peers_message
from funcoin_business.factories.user_factory import UserFactory
from funcoin_business.cars.car_inventory import CarInventory, NoCarsException
from funcoin_business.schema import PeerSchema
from funcoin_business.messages import BaseSchema
from funcoin_business.commands.commands import CommandErrorException

logger = structlog.getLogger(__name__)


class Server:

    def __init__(self, blockchain: Blockchain, connection_pool: ConnectionPool,
                 p2p_protocol, controller):
        self.blockchain = blockchain
        self.connection_pool = connection_pool
        self.p2p_protocol = p2p_protocol(self)
        self.controller = controller(self)
        self.is_waiting_for_authorization = False
        self.voter = None
        self.external_ip = None
        self.external_port = None
        self.cars = CarInventory()

    @staticmethod
    async def close_connection(writer: asyncio.StreamWriter):
        writer.close()
        await writer.wait_closed()

    async def close_connection_unauthorized_user(self, writer: asyncio.StreamWriter):
        await self.close_connection(writer)
        self.is_waiting_for_authorization = False
        return None

    async def close_connection_authorized_user(self, user: funcoin_business.user.User):
        await self.close_connection(user.get_writer())
        self.connection_pool.remove_peer(user)
        self.voter.notify_user_quit()
        return None

    async def wait(self, writer: asyncio.StreamWriter) -> None:
        writer.write("Please wait, another user in the process of connecting\r\n".encode())
        # wait until the process is finished
        while self.is_waiting_for_authorization:
            await asyncio.sleep(5)

    async def load_user_address(self, writer: asyncio.StreamWriter, reader: asyncio.StreamReader):
        # Get user's address
        address = {}
        address["ip"], address["port"] = await get_fake_ip_and_port(reader, writer)
        final_address = None
        try:
            # Configure the address
            final_address = Address().load(address)
        except (MarshmallowError, json.decoder.JSONDecodeError) as e:
            logger.info("Received unauthorized IP and port", peer=writer)
            # Close the connection and clean up
            return await self.close_connection_unauthorized_user(writer)
        else:
            return final_address

    async def conduct_vote(self, user_to_validate: funcoin_business.user.User) -> bool:
        size = self.connection_pool.get_size()
        if size == 0:
            return True

        await self.connection_pool.broadcast(
            f"New user [ip:{user_to_validate.get_ip()}, port: {user_to_validate.get_port()}] is "
            f"requesting for authorization\r\nrespond with {self.voter.authorization_word} for permission"
        )

        while not self.voter.is_vote_ended():
            await asyncio.sleep(5)
            # User as disconnected during the vote
            if user_to_validate.get_reader().at_eof():
                await self.connection_pool.broadcast(f"The user has quit during the vote")
                return False

        # User as disconnected during the vote
        if user_to_validate.get_reader().at_eof():
            return False
        return self.voter.conclude_vote()

    async def get_authorization_response(self, user: funcoin_business.user.User) -> bool:
        await user.receive_message("waiting for authorization")
        # Conduct a vote about user authorization
        if await self.conduct_vote(user):
            # User is authorized
            await user.receive_message("you are now authorized")
            return True

        await user.receive_message("You are not authorized")
        return False

    async def handle_message(self, user: funcoin_business.user.User):
        if self.is_waiting_for_authorization and not self.voter.has_user_vote(user):
            await user.receive_message("Unauthorized user requesting access please make your vote")
            message = await user.respond()
            await user.receive_message("decision received")
            self.voter.add_vote(message, user.get_address())
        else:
            await user.receive_message("respond:")
            message = await user.respond()
            print("message accepted: ", message)
            if message == "size":
                print(self.connection_pool.get_size())

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """

        :param reader: asyncio.StreamReader
        :param writer: asyncio.StreamWriter, represents the connecting peer
        :return:
        """
        # If the server is already in authorization process
        if self.is_waiting_for_authorization:
            # wait until authorization process ends
            await self.wait(writer)

        # Start of authorization process
        self.is_waiting_for_authorization = True
        authorization_word = 'p'
        self.voter = Voter(self.connection_pool.get_size(), authorization_word)

        try:
            # Get user's address: {ip,port}
            address = await self.load_user_address(writer, reader)

            user = User(writer, reader, 100, False, address)
            print("address:", type(user.get_port()))

            # Wait for authorization process to finish
            if await self.get_authorization_response(user):
                # User is authorized
                self.connection_pool.add_peer(user)
            # User is not authorized
            else:
                return await self.close_connection_unauthorized_user(writer)

            # End of authorization process
            self.is_waiting_for_authorization = False
        except (asyncio.exceptions.IncompleteReadError, ConnectionError):
            return await self.close_connection_unauthorized_user(writer)

        # User is authorized
        try:
            while True:
                # Handle user message
                await self.handle_message(user)

                await writer.drain()
                if writer.is_closing():
                    break

        except (asyncio.exceptions.IncompleteReadError, ConnectionError):
            # TODO: check if ignored exception will work too.
            return await self.close_connection_authorized_user(user)

        # The connection has close, close and clean up
        await self.close_connection_authorized_user(user)

    async def listen(self, hostname="0.0.0.0", port="8888"):
        # This is the listen method which spawns our server
        server = await asyncio.start_server(self.handle_connection, hostname, port)
        logger.info(f"Server listening on {hostname}:{port}")

        async with server:
            await server.serve_forever()


class Voter:
    def __init__(self, size: int, authorization_word: str):
        self.votes = {}
        self.end_of_vote = size
        self.vote_ended = False
        self.authorization_word = authorization_word

    def is_vote_ended(self) -> bool:
        return self.vote_ended

    def has_user_vote(self, user: funcoin_business.user.User):
        return user.get_address() in self.votes.keys()

    def add_vote(self, vote: str, address: str) -> None:
        self.votes[address] = vote
        self.check_vote_ended()

    def conclude_vote(self) -> bool:
        yes_voters = list(self.votes.values()).count(self.authorization_word)
        if yes_voters >= len(self.votes) / 2.0:
            return True
        return False

    def notify_user_quit(self):
        self.end_of_vote -= 1
        self.check_vote_ended()

    def check_vote_ended(self):
        if len(self.votes) == self.end_of_vote:
            self.vote_ended = True

# {"ip": "1234", "port": 8888}
# telnet 127.0.0.1 8888
