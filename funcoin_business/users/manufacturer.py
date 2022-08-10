import asyncio
import json.decoder
from textwrap import dedent

from marshmallow.exceptions import MarshmallowError

from funcoin_business.commands.commands import Command
from funcoin_business.schema import CarSchema
from funcoin_business.users.authorized_user import AuthorizedUser
from funcoin_business.cars.car import Car
from funcoin_business.users.dealer import Dealer


class Manufacturer(AuthorizedUser):
    """
    Class Manufacturer inherits from class User, handles users on the server with a manufacturer access
    Authorized Actions:
    - Can view his car inventory
    - Can make a transaction of a car to another user with Dealer access
    - Can create new cars
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
        self.access = AuthorizedUser.manufacturer

    @staticmethod
    async def get_actions_menu() -> str:
        """
        Static Method
        :return: Str, representing the actions a Manufacturer can do and a short explanation about each action
        """
        message = dedent(f"""
                \r===            
                \rPlease choose the required action: 
                 \r- /transaction will make a transaction of a car to a dealer.
                 \r- /car will create a new car
                 \r- /view will show all the cars in your possession.
                \r===
                """)
        return message

    @property
    async def get_next_in_chain(self) -> str:
        """
        :return: the type of access a Manufacturer can transact with.
        """
        return AuthorizedUser.dealer

    async def __create_car(self, _) -> tuple[Command, CarSchema]:
        """
        Creates a new Car using schema.CarSchema with input from the user.
        :param _: Any, ignorable
        :return:
        """
        # Initialize the owner of the car
        owner = {"address": self.get_address(), "access": self.get_access()}

        # Get all other information of the car from the user
        while True:
            await self.receive_message("Please enter the ID of the car:")
            ID = await self.respond()
            await self.receive_message("Please enter the model of the car:")
            model = await self.respond()
            await self.receive_message("Please enter the color of the car:")
            color = await self.respond()
            try:
                car = CarSchema().load({"id": ID, "owner": owner, "model": model, "color": color})
                break
            except (MarshmallowError, json.decoder.JSONDecodeError):
                await self.receive_message("There is a problem with the car details, please try again")
                # return Command.ERROR, "There is a problem with the car details, please try again"

        await self.receive_message("Car was successfully created")
        # Add the car to the user's car inventory
        await self.add_car(Car(**car))
        return Command.NEW_CAR, car

    async def make_action(self, dealers: dict[str, Dealer]) -> tuple[Command, Command | str | dict | CarSchema]:
        """
        Lets the user choose an action from his actions' menu and performs the action

        :param dealers: dict {str: "ip:port", Dealer(object)}
        :return: tuple, if an error occurred return: (Command.Error, str: the error),
        if a transaction occurred return: (Command.Transaction, dict: TransactionSchema)
        if a new car was created return: (Command.New_Car, CarSchema)
        if no further action is required return: (Command.SUCCESS, Command.SUCCESS)
        """
        actions = {"/transaction": self.transaction, "/car": self.__create_car, "/view": self.view_cars}
        selected_action = await self.choose_action(actions, await self.get_actions_menu())
        return await selected_action(dealers)
