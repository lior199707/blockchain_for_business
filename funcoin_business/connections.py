import structlog
from more_itertools import take

from funcoin_business.users.user import User
from funcoin_business.users.authorized_user import AuthorizedUser

logger = structlog.getLogger(__name__)


class ConnectionPool:
    """
    Class ConnectionPool handles all the users connected to the server
    has a dictionary with:
    keys - user addresses (ip:port)
    value - the user, funcoin_business.user.User
    """

    def __init__(self):
        self.connection_pool = dict()

    async def broadcast(self, message: str) -> None:
        """
        sends a message to all the user connected to the server
        :param message:  the message to send
        """
        for user in list(self.connection_pool.values()):
            await user.receive_message(message)

    def add_peer(self, user: User) -> None:
        """adds a user to the dictionary of the connected users"""
        address = user.get_address()
        self.connection_pool[address] = user
        logger.info("Added new peer to pool", address=address)

    def remove_peer(self, user: User) -> None:
        """Removes a user from the dictionary of the connected users"""
        address = user.get_address()
        self.connection_pool.pop(address)
        logger.info("Removed peer from pool", address=address)

    def get_alive_peers(self, count: int) -> list:
        """

        :param count: the number of wanted users.
        :return: list containing the first 'count' users in the pool
        """
        # TODO (Reader): Sort these by most active,
        #  but let's just get the first *count* of them for now
        return take(count, self.connection_pool.items())
        # return [user.address for user in list(self.connection_pool.values())[:count]]

    def get_size(self) -> int:
        """

        :return: The number of authorized users connected to the server
        """
        return len(self.connection_pool)

    def get_access_dict(self, required_access: str):
        """
        The method returns a dict of "ip:port": user(Class)
        containing all the connected users whose access is the required access.
        for example if the required access is Dealer returns a dict with all the connected dealers.

        :param required_access: The access of the user's next_in_chain
        :return: dict, containing all connected users whose access is the required access
        """
        return {key: user for key, user in self.connection_pool.items() if user.get_access() == required_access}
        # return [user for user in list(self.connection_pool.values()) if user.get_access() == required_access]
