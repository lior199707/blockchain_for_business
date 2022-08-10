import asyncio
from textwrap import dedent

from funcoin_business.cars.car import Car
from funcoin_business.users.authorized_user import AuthorizedUser
from funcoin_business.commands.commands import Command


class ScrapMerchant(AuthorizedUser):
    """
    Class ScrapMerchant inherits from class User, handles users on the server with scrap merchant access
    Authorized Actions:
    - Can view his car inventory
    - Can make a transaction of a car to another user with Dealer access
    - Can destroy a car
    """
    def __init__(self, writer: asyncio.StreamWriter, reader: asyncio.StreamReader, amount: float, miner: bool,
                 address: dict):
        super().__init__(writer, reader, amount, miner, address)
        """

        :param writer: asyncio.StreamWriter
        :param reader: asyncio.StreamReader
        :param amount: float, the amount of money
        :param miner: bool, indicates if the user is a miner
        :param address: dict(schema.AddressSchema), {"ip": ip, "port": port}
        """
        self.access = AuthorizedUser.scrap_merchant

    @property
    async def get_next_in_chain(self) -> None:
        """

        :return: None, scrap merchant can't make transactions.
        """
        return None

    @staticmethod
    async def get_actions_menu() -> str:
        """
        Static Method
        :return: Str, representing the actions a ScrapMerchant can do and a short explanation about each action
        """
        message = dedent(f"""
                    \r===            
                    \rPlease choose the required action: 
                     \r- /destroy will destroy the car of your choice
                     \r- /view will show all the cars in your possession.
                    \r===
                    """)
        return message

    async def __destroy_car(self, _) -> tuple[Command, str | Car]:
        """
        Lets the user destroy a car from his inventory

        :param _: Any, ignorable
        :return: if the user has no cars return: (Command.ERROR, str: the error),
        otherwise return: (Command.DESTROY_CAR, Car(object): the car to destroy)
        """
        await self.receive_message("destroying a car")
        # If the user has no cars
        if not self.has_cars():
            return Command.ERROR, "You have no cars in your possession"

        # Choose the car to destroy
        car = await self.choose_car_from_inventory()

        # Remove the car from the car inventory
        await self.remove_car(str(car.get_id()))
        return Command.DESTROY_CAR, car

    async def make_action(self, _) -> tuple[Command, Command | str | Car]:
        """
        Lets the user choose an action from his actions' menu and performs the action

        :param _: Any, ignorable
        :return: tuple, if an error occurred return: (Command.Error, str: the error)
        if a car was destroyed return: (Command.DESTROY_CAR, Car(object): the car to destroy)
        if no further action is required return: (Command.SUCCESS, Command.SUCCESS)
        """
        actions = {"/destroy": self.__destroy_car, "/view": self.view_cars}
        selected_action = await self.choose_action(actions, await self.get_actions_menu())

        return await selected_action(_)
