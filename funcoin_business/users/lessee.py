import asyncio
from textwrap import dedent

from funcoin_business.users.authorized_user import AuthorizedUser
from funcoin_business.users.scrap_merchant import ScrapMerchant
from funcoin_business.commands.commands import Command


class Lessee(AuthorizedUser):
    """
    Class Lessee inherits from class User, handles users on the server with a lessee access
    Authorized Actions:
    - Can view his car inventory
    - Can make a transaction of a car to another user with ScrapMerchant access
    """

    def __init__(self, writer: asyncio.StreamWriter, reader: asyncio.StreamReader, amount: float, miner: bool,
                 address: dict):
        """

        :param writer: asyncio.StreamWriter
        :param reader: asyncio.StreamReader
        :param amount: float, the amount of money
        :param miner: bool, indicates if the user is a miner
        :param address: dict(schema.AddressSchema), {"ip": ip, "port": port}
        """
        super().__init__(writer, reader, amount, miner, address)
        self.access = AuthorizedUser.lessee

    @property
    async def get_next_in_chain(self) -> str:
        """

        :return: the type of access a Lessee can transact with.
        """
        return AuthorizedUser.scrap_merchant

    @staticmethod
    async def get_actions_menu():
        """
        Static Method
        :return: Str, representing the actions a Lessee can do and a short explanation about each action
        """
        message = dedent(f"""
                \r===            
                \rPlease choose the required action: 
                 \r- /transaction will make a transaction of a car to a leasing company.
                 \r- /view will show all the cars in your possession.
                \r===
                """)
        return message

    async def make_action(self, scrap_merchants: dict[str, ScrapMerchant]) -> tuple[Command, Command | str | dict]:
        """
        Lets the user choose an action from his actions' menu and performs the action

        :param scrap_merchants: dict {str: "ip:port", ScrapMerchant(object)}
        :return: tuple, if an error occurred return: (Command.Error, str: the error),
        if a transaction occurred return: (Command.Transaction, dict: TransactionSchema)
        if no further action is required return: (Command.SUCCESS, Command.SUCCESS)
        """
        actions = {"/transaction": self.transaction, "/view": self.view_cars}
        selected_action = await self.choose_action(actions, await self.get_actions_menu())
        return await selected_action(scrap_merchants)
