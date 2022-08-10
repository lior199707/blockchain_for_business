from funcoin_business.server import Server
from funcoin_business.commands.commands import Command, CommandErrorException
from copy import copy
from funcoin_business.cars.car import Car
from funcoin_business.messages import create_transaction_message, BaseSchema
from funcoin_business.schema import TransactionSchema, CarSchema
from funcoin_business.blockchain import Blockchain


class Controller:
    """
    Class controller, perform actions on the server and the blockchain, based on commands derives from users actions.
    """

    def __init__(self, server: Server):
        self.server = server

    async def handle_command(self, command: Command, value: str | CarSchema | TransactionSchema) -> None:
        """
        Handles commands derived from user actions

        :param command: Command(Enum), the command to handle
        :param value: the value matching to the command
        """
        commands = {
            Command.ERROR: self.handle_error,
            Command.NEW_CAR: self.handle_new_car,
            Command.TRANSACTION: self.handle_transaction,
            Command.DESTROY_CAR: self.handle_destroy_car,
        }
        handler = commands.get(command)
        if handler:
            await handler(value)
        else:
            raise CommandErrorException("Invalid command")

    async def handle_transaction(self, transaction: TransactionSchema()) -> None:
        """
        Handles transaction command, a transaction made by a user.

        :param transaction: TransactionSchema, the transaction details.
        """
        # load sender receiver and car
        sender = self.server.connection_pool.get_authorized_user(transaction["sender"])
        receiver = self.server.connection_pool.get_authorized_user(transaction["receiver"])
        car = self.server.cars.get_car(str(transaction["item"]["id"]))
        if not (sender and receiver and car):
            raise CommandErrorException("Invalid transaction, there was a problem with on of the details")

        # Delete the car from the sender cars inventory
        await sender.remove_car(str(car.get_id()))
        # Transfer ownership of the car to the receiver
        car.set_owner(receiver.get_address(), receiver.access)
        await receiver.add_car(copy(car))

        # Add the transaction to the blockchain
        self.server.blockchain.new_transaction(transaction)

        # Create a transaction message and broadcast it to all connected users.
        transaction_message = create_transaction_message(self.server.external_ip, self.server.external_port, transaction)
        message = BaseSchema().loads(transaction_message)
        await self.server.p2p_protocol.handle_message(message["message"])

    async def handle_new_car(self, car: CarSchema()) -> None:
        """
        Handles new car command, a creation of a new car.

        :param car:
        """
        car_obj = Car(**car)
        # Add the car to the server's car inventory
        self.server.cars.add_car(car_obj)
        # Broadcast a message to all connected users about the new car.
        message = f"A new car was created:\r\n{str(car_obj)}"
        await self.server.connection_pool.broadcast(message)

    async def handle_error(self, error: str) -> None:
        """
        Handles an error command, error that happened
        :raise: CommandErrorException

        :param error: Str, representing the error that happened
        """
        raise CommandErrorException(error)

    async def handle_destroy_car(self, car: Car) -> None:
        """
        Handles destroy car command, a car that was destroyed.
        :param car: Car(object), the car to destroy
        """
        # Remove the car from the server's inventory and broadcast a message about it to all connected users.
        await self.server.cars.remove_car(str(car.get_id()))
        message = f"A car was destroyed:\r\n{str(car)}"
        await self.server.connection_pool.broadcast(message)
