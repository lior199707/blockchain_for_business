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
from funcoin_business.users.authorized_user import AuthorizedUser

logger = structlog.getLogger(__name__)


class Server:
    """
    Class Server, runs asyncio.start_server, the server contains a lisr of authorized users and a blockchain.
    """

    def __init__(self, blockchain: Blockchain, connection_pool: ConnectionPool,
                 p2p_protocol, controller):
        self.blockchain = blockchain
        self.connection_pool = connection_pool
        self.p2p_protocol = p2p_protocol(self.connection_pool)
        self.controller = controller(self)
        self.is_waiting_for_authorization = False
        self.voter = None
        self.external_ip = None
        self.external_port = None
        self.cars = CarInventory()

    @staticmethod
    async def close_connection(writer: asyncio.StreamWriter) -> None:
        """
        Closes the connection of the user.
        :param writer: asyncio.StreamWriter, the writer of the user.
        """
        writer.close()
        await writer.wait_closed()

    @staticmethod
    async def get_user_access(user: User) -> str:
        message = f"Please choose your role:\r\n" \
                  f"[{AuthorizedUser.manufacturer}, {AuthorizedUser.lessee}, {AuthorizedUser.dealer}," \
                  f"{AuthorizedUser.scrap_merchant}, {AuthorizedUser.leasing_company}]\r\n" \
                  f"Please type anything else for guest access\r\n"
        await user.receive_message(message)
        return await user.respond()

    @staticmethod
    async def send_welcome_message(user: User) -> None:
        """
        Sends a welcome message to a newly connected client
        :param user: the user to send welcome message to.
        :return:
        """
        message = dedent(f"""
        \r===            
        \rHelp: 
         \r- /action will show your available actions
         \r- /size will show the number of connected users
         \r- /access will show your role in the chain
         \r- /info will show you information about the cars
        \r===
        """)
        await user.receive_message(message)

    async def close_connection_unauthorized_user(self, writer: asyncio.StreamWriter) -> None:
        """
        Closes the connection for unauthorized user.
        :param writer: syncio.StreamWriter, the writer of the user.
        :return: None
        """
        await self.close_connection(writer)

        # Indicating there isn't a user who is waiting for authorization.
        self.is_waiting_for_authorization = False
        return None

    async def close_connection_authorized_user(self, user: User) -> None:
        """
        Closes the connection for authorized user.
        :param user: User, the user.
        :return: None
        """
        # TODO: REMOVE THE CARS OF THE USER FROM THE SERVERS CAR INVENTORY
        await self.close_connection(user.get_writer())

        # Remove the user from the connections pool
        self.connection_pool.remove_peer(user)

        # Notify the voter a user has left, so if the server is during a vote the vote will be able to end.
        await self.voter.notify_user_quit()
        return None

    async def wait(self, writer: asyncio.StreamWriter) -> None:
        """
        Makes a user wait until the authorization process of another user is finished.
        :param writer: asyncio.StreamWriter, the writer of the user.
        """
        writer.write("Please wait, another user in the process of connecting\r\n".encode())
        # wait until the process is finished
        while self.is_waiting_for_authorization:
            await asyncio.sleep(5)

    def get_external_ip(self) -> str:
        """

        :return: the external ip of the user.
        """
        return self.external_ip

    def get_external_port(self) -> int:
        """

        :return: the external port the user is listening to.
        """
        return self.external_port

    async def __load_user_address(self, writer: asyncio.StreamWriter, reader: asyncio.StreamReader):
        """
        Gets as keyboard input the ip and port of the user and tries to load it, if exception was raised.
        closes the connection of the user.
        :param writer: asyncio.StreamWriter.
        :param reader: asyncio.StreamReader.
        :return: schema.AddressSchema(dict), the address of the user, if the address isn't valid returns None.
        """
        # Get user's address
        address = {}
        address["ip"], address["port"] = await get_fake_ip_and_port(reader, writer)
        final_address = None
        try:
            # Configure the address
            final_address = AddressSchema().load(address)
        except (MarshmallowError, json.decoder.JSONDecodeError) as e:
            logger.info("Received unauthorized IP and port", peer=writer)
            # Close the connection and clean up
            return await self.close_connection_unauthorized_user(writer)
        else:
            return final_address

    async def conduct_vote(self, user_to_validate: User, access: str) -> bool:
        """
        Conducts an authorization vote in the server.
        :param access: str, the role of the user in the blockchain.
        :param user_to_validate: the user wants to join the network.
        :return: True if the user is authorized, False otherwise.
        """
        size = self.connection_pool.get_size()
        if size == 0:
            return True

        # Indicate all the users that a new user is requesting to join.
        await self.connection_pool.broadcast(
            f"New user [ip:{user_to_validate.get_ip()}, port: {user_to_validate.get_port()}] is "
            f"requesting for authorization as {access}\r\n"
            f"respond with {self.voter.authorization_word} for permission when asked to make your vote"
        )

        # Wait until the vote ends.
        while not self.voter.is_vote_ended():
            await asyncio.sleep(5)
            # New user as disconnected during the vote
            if user_to_validate.get_reader().at_eof():
                await self.connection_pool.broadcast(f"The user has quit during the vote")
                return False

        # User as disconnected during the vote
        if user_to_validate.get_reader().at_eof():
            return False
        return self.voter.conclude_vote()

    async def handle_authorization_response(self, user: User, access: str) -> bool:
        """
        Handles the result of a vote on the server.
        :param access: str, the role of the user in the blockchain.
        :param user: New user joining the server.
        :return: True if the user is authorized, False otherwise.
        """
        await user.receive_message("waiting for authorization")

        # Conduct a vote about user authorization
        if await self.conduct_vote(user, access):
            # User is authorized
            await user.receive_message("you are now authorized")
            return True

        # User is not authorized
        await user.receive_message("You are not authorized")
        return False

    async def handle_pending_transactions(self, user: AuthorizedUser) -> None:
        """
        Handles an authorized user who has pending transactions
        :param user: the authorized user.
        :return:
        """

        user_choice = 'y'
        await user.receive_message("You have pending transaction waiting for your approval, would you like to"
                                   "attend them?(y / n)")
        while True:
            answer = await user.respond()
            if answer == "n":
                return
            elif answer == "y":
                break
            await user.receive_message("Invalid input, please try again")

        # user handles his pending transactions
        # get the first pending transaction of the user
        # TODO: get the unapproved transactions list and let the controller handle it
        #  (change the car.is_in_pending_transaction value to false because the transaction was denied)
        approved_transactions = await user.handle_pending_transaction()
        for at in approved_transactions:
            try:
                await self.controller.handle_approved_transaction(at)
            except CommandErrorException as e:
                await user.receive_message(str(e))

    async def handle_user_input(self, user) -> None:
        """
        Handles user input according to the server's state.(regular state or vote state)
        :param user: User(object), The user that sent the message.
        """

        # If the server is on a vote and the user hasn't voted yet
        if self.is_waiting_for_authorization and not self.voter.has_user_vote(user):
            await user.receive_message("Unauthorized user requesting access please make your vote")
            message = await user.respond()
            await user.receive_message("decision received")
            await self.voter.add_vote(message, user.get_address())
            # TODO: finish the transaction update
        if isinstance(user, AuthorizedUser):
            if user.has_pending_transactions():
                await self.handle_pending_transactions(user)

        await user.receive_message("respond:")
        message = await user.respond()
        if message == "/action":
            try:
                command, value = await user.make_action(
                    self.connection_pool.get_access_dict(await user.get_next_in_chain))
            except NotImplementedError:
                await user.receive_message("You are not allowed to make actions")
                return None
            try:
                await self.controller.handle_command(command, value)
            except CommandErrorException as e:
                await user.receive_message(str(e))
        elif message == "/size":
            print(self.connection_pool.get_size())
        elif message == "/access":
            await user.receive_message(f"Your access is: {user.get_access()}")
        elif message == "/info":
            try:
                await user.receive_message(self.cars.view_cars())
            except NoCarsException as e:
                await user.receive_message(str(e))

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """

        :param reader: asyncio.StreamReader
        :param writer: asyncio.StreamWriter, represents the connecting peer
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
            address = await self.__load_user_address(writer, reader)

            user = User(writer, reader, 100, False, address)

            # Get user's access
            access = await self.get_user_access(user)

            # Wait for authorization process to finish
            if await self.handle_authorization_response(user, access):
                # User is authorized
                user = await UserFactory().get_user(access, writer, reader, 100, False, address)
                peer_message = create_peers_message(self.get_external_ip(), self.get_external_port(),
                                                    PeerSchema().load({"address": address}))
                peer_message = BaseSchema().loads(peer_message)
                await self.p2p_protocol.handle_message(peer_message["message"])
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
            await self.send_welcome_message(user)
            while True:
                # Handle user input according to server's state
                await self.handle_user_input(user)

                await writer.drain()
                if writer.is_closing():
                    break

        except (asyncio.exceptions.IncompleteReadError, ConnectionError):
            # TODO: check if ignored exception will work too.
            return await self.close_connection_authorized_user(user)

        # The connection has close, close and clean up
        await self.close_connection_authorized_user(user)

    async def listen(self, hostname="0.0.0.0", port="8888") -> None:
        """
        This is the listen method which spawns our server
        """
        server = await asyncio.start_server(self.handle_connection, hostname, port)
        logger.info(f"Server listening on {hostname}:{port}")

        self.external_ip = await get_external_ip()
        self.external_port = 8888

        async with server:
            await server.serve_forever()


class Voter:
    """
    Class Voter, handles votes on the server.
    Only authorized users can vote.
    """

    def __init__(self, size: int, authorization_word: str):
        self.votes = {}
        self.end_of_vote = size
        self.vote_ended = False
        self.authorization_word = authorization_word

    def is_vote_ended(self) -> bool:
        """
        Should be in track of this method returned bool, it indicates if the vote was ended or not
        can be used with while loop
        while not is_vote_ended:
            sleep
        :return: True if vote ended, False otherwise.
        """
        return self.vote_ended

    def has_user_vote(self, user: User) -> bool:
        """
        checks if a user has already voted.
        :param user: The user.
        :return: True if the user has already voted, False otherwise.
        """
        return user.get_address() in self.votes.keys()

    async def add_vote(self, vote: str, address: str) -> None:
        """
        Adds user's vote.
        :param vote: Str, the answer for the vote
        :param address: the address if the user that voted.
        """
        self.votes[address] = vote

        # Check if the vote has ended
        await self.check_vote_ended()

    def conclude_vote(self) -> bool:
        """
        Calculates the decision of the vote based on the votes.
        :return: True if the vote has passed(more than half of the users was in favor), False otherwise.
        """
        yes_voters = list(self.votes.values()).count(self.authorization_word)
        if yes_voters >= len(self.votes) / 2.0:
            return True
        return False

    async def notify_user_quit(self) -> None:
        """
        notifies the voter an authorized user has left during the vote.
        """
        self.end_of_vote -= 1

        # Checks if the vote has ended
        await self.check_vote_ended()

    async def check_vote_ended(self) -> None:
        """
        Checks if the vote ended by the number of votes currently held by the Voter.
        If the vote ended changes the voter vote_ended attribute to True.
        """
        if len(self.votes) == self.end_of_vote:
            self.vote_ended = True

# {"ip": "1234", "port": 8888}
# telnet 127.0.0.1 8888
