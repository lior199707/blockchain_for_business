from asyncio import StreamReader, StreamWriter
from abc import ABC

from nacl.signing import SigningKey
from nacl.encoding import HexEncoder

from funcoin_business.cars.car import Car
from funcoin_business.cars.car_inventory import NoCarsException
from funcoin_business.users.user import User
from funcoin_business.commands.commands import Command
from funcoin_business.cars.car_inventory import CarInventory


class AuthorizedUser(User, ABC):
    """
    Abstract Class AuthorizedUser, handles authorized users
    static variables:
    AuthorizedUser.manufacturer - user manufacturer access
    AuthorizedUser.dealer - user dealer access
    AuthorizedUser.leasing_company - user leasing_company access
    AuthorizedUser.lessee - user lessee access
    AuthorizedUser.scrap_merchant - user scrap_merchant access
    """

    # Access types of users
    manufacturer = "Manufacturer"
    dealer = "Dealer"
    leasing_company = "Leasing Company"
    lessee = "Lessee"
    scrap_merchant = "Scrap Merchant"

    def __init__(self, writer: StreamWriter, reader: StreamReader, amount: float, miner: bool,
                 address: dict):
        """

        :param writer: asyncio.StreamWriter
        :param reader: asyncio.StreamReader
        :param amount: float, the amount of money
        :param miner: bool, indicates if the user is a miner
        :param address: dict(schema.AddressSchema), {"ip": ip, "port": port}
        """
        super().__init__(writer, reader, amount, miner, address)
        self.cars = CarInventory()
        self.private_key = SigningKey.generate()

    async def __choose_user_for_transaction(self,
                                            access_dict: dict[str, 'AuthorizedUser'],
                                            next_in_chain: str
                                            ) -> 'AuthorizedUser':
        """
        Private Method
        Asks the user to choose another user he wants to transact with(according to transaction rules) by entering the
        ip:port of the selected user.

        :param access_dict: Dict {"ip:port": user(object)}, all users in the dict should have the same access.
        :param next_in_chain: Str, the type of access the user can transact with.
        :return: User derived class, the user to transact with.
        """
        # Print to the user all the ip:port of the users he can transact with
        message = f"connected {next_in_chain + 's'}:\r\n"
        for key, user in access_dict.items():
            message += f"ip: {user.get_ip()}  port: {user.get_port()}\r\n"
        message += f"Please enter the ip and port of the selected {next_in_chain} in this format: ip:port, i.e 1:1"
        await self.receive_message(message)
        # Get the choice of the user to transact with
        while True:
            key = await self.respond()
            chosen_user = access_dict.get(key)
            if chosen_user:
                break
            await self.receive_message("unrecognized ip and port, please try again")
        await self.receive_message(f"The {next_in_chain} you selected: {chosen_user.get_address()}")
        return chosen_user

    async def choose_car_from_inventory(self) -> Car:
        """
        Lets the user choose a car from his car inventory
        :return: Car(object), the car the user chose
        """
        await self.receive_message(f"The cars:\r\n{str(self.cars)}\r\nPlease enter the id of the car you wish to select")
        while True:
            ID = await self.respond()
            car_for_transaction = self.cars.get_car(ID)
            if car_for_transaction:
                return car_for_transaction
            await self.receive_message("Unrecognized car id, please try again")

    async def transaction(self,
                          access_dict: dict[str, 'AuthorizedUser']
                          ) -> tuple[Command, str | dict]:
        """
        Creates a new transaction of a car chosen by the user to a Dealer.
        :param access_dict: dict containing all the connected users with specific access that the user can transact with
        :return: tuple, if an error occurred return: (Command.Error, str: the error),
        otherwise return: (Command.Transaction, dict: TransactionSchema)
        """
        from funcoin_business.transactions.transactions import create_transaction

        if not self.has_cars():
            return Command.ERROR, "You have no cars in your possession"

        # If there are no connected users with the access required.
        if len(access_dict) == 0:
            return Command.ERROR, f"No {await self.get_next_in_chain + 's'} connected found"

        # Choose a user and a car for the transaction
        await self.receive_message("creating a transaction")
        transaction_partner = await self.__choose_user_for_transaction(access_dict, await self.get_next_in_chain)
        transaction_car = await self.choose_car_from_inventory()

        if not transaction_partner and transaction_car:
            return Command.ERROR, "Something went wrong with the transaction"

        return Command.TRANSACTION, create_transaction(self, transaction_partner, transaction_car)

    async def choose_action(self, actions_dict: dict[str, classmethod], actions_menu: str) -> classmethod:
        """
        Lets the user choose an action from the actions he is authorized to perform

        :param actions_dict: dict, {str: the string representing the action, class-method: the method for the action}
        :param actions_menu: str, every user holds his own actions' menu: self.get_actions_menu
        :return: class-method, the selected action to perform
        """
        # Presents the user with his actions menu
        await self.receive_message(actions_menu)

        # Get the selected action
        while True:
            action = await self.respond()
            selected_action = actions_dict.get(action)
            if selected_action:
                break
            await self.receive_message("Unknown action, please try again")
        return selected_action

    async def view_cars(self, _) -> tuple[Command, Command | str]:
        """
        Presents the user with the cars he owns.

        :param _: Any(can be None), the parameter is not used
        :return: tuple, if the user has no cars in his inventory return: (Command.ERROR, str: the error)
        otherwise return: (Command.SUCCESS, Command.SUCCESS) indicating no further actions should be done
        """
        try:
            message = self.cars.view_cars()
        except NoCarsException as e:
            return Command.ERROR, str(e)

        await self.receive_message(message)
        return Command.SUCCESS, Command.SUCCESS

    def has_cars(self) -> bool:
        """
        :return: Boolean, indicating if the users has cars in his inventory, True if he has cars False if not
        """
        return self.cars.has_cars()

    async def add_car(self, car: Car) -> None:
        """
        Adds a car to the user's car inventory
        :param car: Car(object), the car to add to the inventory
        """
        self.cars.add_car(car)

    async def remove_car(self, car_id: str) -> bool:
        """
        Removes a car from the user's car inventory
        :param car_id: str, the id of the car to remove (id is unique)
        :return: true if succeeded to remove the car from user's inventory, false otherwise
        """
        return await self.cars.remove_car(car_id)

    def get_public_key(self) -> bytes:
        """
        :return: <bytes>, encoded verification key of the user, used to verify the user's signatures
        """
        return self.private_key.verify_key.encode(encoder=HexEncoder)

    def sign(self, data: bytes) -> str:
        """
        Lets the user sign on transactions.

        :param data: bytes, the data to sign on
        :return: str, representing the encoded signature of the user
        """
        signature = self.private_key.sign(data).signature
        return HexEncoder.encode(signature).decode("ascii")
