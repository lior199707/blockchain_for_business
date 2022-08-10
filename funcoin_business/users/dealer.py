import asyncio
from textwrap import dedent

from funcoin_business.users.authorized_user import AuthorizedUser
from funcoin_business.schema import AddressSchema
from funcoin_business.commands.commands import Command
from funcoin_business.users.leasing_company import LeasingCompany


class Dealer(AuthorizedUser):
    """
    Class Dealer inherits from class AuthorizedUser, handles users on the server with dealer access
    Authorized Actions:
    - Can view his car inventory
    - Can make a transaction of a car to another user with Leasing Company access
    """

    def __init__(self, writer: asyncio.StreamWriter, reader: asyncio.StreamReader, amount: float, miner: bool,
                 address: AddressSchema()):
        """

        :param writer: asyncio.StreamWriter
        :param reader: asyncio.StreamReader
        :param amount: float, the amount of money
        :param miner: bool, indicates if the user is a miner
        :param address: dict(schema.AddressSchema), {"ip": ip, "port": port}
        """
        super().__init__(writer, reader, amount, miner, address)
        self.access = AuthorizedUser.dealer

    @property
    async def get_next_in_chain(self) -> str:
        """
        :return: Str, the type of access a Dealer can transact with.
        """
        return AuthorizedUser.leasing_company

    @staticmethod
    async def get_actions_menu() -> str:
        """
        Static Method
        :return: Str, representing the actions a Dealer can do and a short explanation about each action
        """
        message = dedent(f"""
                \r===            
                \rPlease choose the required action: 
                 \r- /transaction will make a transaction of a car to a leasing company.
                 \r- /view will show all the cars in your possession.
                \r===
                """)
        return message

    async def make_action(self, leasing_companies: dict[str, LeasingCompany]) -> tuple[Command, Command | str | dict]:
        """
        Lets the user choose an action from his actions' menu and performs the action

        :param leasing_companies: dict {str: "ip:port", LeasingCompany(object)}
        :return: tuple, if an error occurred return: (Command.Error, str: the error),
        if a transaction occurred return: (Command.Transaction, dict: TransactionSchema)
        if no further action is required return: (Command.SUCCESS, Command.SUCCESS)
        """
        actions = {"/transaction": self.transaction, "/view": self.view_cars}
        selected_action = await self.choose_action(actions, await self.get_actions_menu())
        return await selected_action(leasing_companies)
