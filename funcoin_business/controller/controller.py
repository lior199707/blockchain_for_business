from funcoin_business.server import Server
from funcoin_business.commands.commands import Command, CommandErrorException
from copy import copy
from funcoin_business.cars.car import Car
from funcoin_business.messages import create_transaction_message, BaseSchema
from funcoin_business.schema import TransactionSchema, CarSchema
from funcoin_business.blockchain import Blockchain
from funcoin_business.transactions.transactions import validate_transaction


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
            Command.SUCCESS: self.handle_success,
        }
        handler = commands.get(command)
        if handler:
            await handler(value)
        else:
            raise CommandErrorException("Invalid command")

    # async def handle_transaction(self, transaction: TransactionSchema()) -> None:

        # # load sender receiver and car
        # sender = self.server.connection_pool.get_authorized_user(transaction["sender"]["address"])
        # receiver = self.server.connection_pool.get_authorized_user(transaction["receiver"]["address"])
        # # loads the car from the server's car list
        # car = self.server.cars.get_car(str(transaction["item"]["id"]))
        # if not (sender and receiver and car):
        #     raise CommandErrorException("Invalid transaction, there was a problem with one or more of the details")
        #
        # # validate the transaction by sender's signature
        # if not validate_transaction(transaction, sender):
        #     await self.server.connection_pool.broadcast("A fraudulent transaction was detected")
        #     return None
        #
        # # Add the transaction to the blockchain
        # # Case invalid transaction
        # if not self.server.blockchain.new_transaction(transaction):
        #     raise CommandErrorException("Transaction was failed")
        #
        # # Delete the car from the sender cars inventory
        # if not await sender.remove_car(str(car.get_id())):
        #     raise CommandErrorException("Transaction was failed, couldn't find the car in your inventory")
        # # Transfer ownership of the car to the receiver
        # car.set_owner(receiver.get_address(), receiver.access)
        # await receiver.add_car(copy(car))
        #
        # # Create a transaction message and broadcast it to all connected users.
        # transaction_message = create_transaction_message(self.server.external_ip, self.server.external_port, transaction)
        # message = BaseSchema().loads(transaction_message)
        # await self.server.p2p_protocol.handle_message(message["message"])
        #
        # # If the number of pending transaction has reached the maximum, create a new block and store it.
        # if self.server.blockchain.is_pending_transactions_full():
        #     # Try to add a new block containing all pending transactions to the blockchain
        #     if not self.server.blockchain.add_block(self.server.blockchain.new_block()):
        #         # If the block is not valid
        #         raise CommandErrorException("Fraudulent Block")
        #     # Broadcast a message to the server about the new block that was added to the blockchain
        #     await self.server.connection_pool.broadcast("A new Block was added to the blockchain")

        :param transaction: TransactionSchema, the transaction details.
        """
        # load sender receiver and car
        sender = self.server.connection_pool.get_authorized_user(transaction["sender"]["address"])
        receiver = self.server.connection_pool.get_authorized_user(transaction["receiver"]["address"])
        # loads the car from the server's car list
        car = self.server.cars.get_car(str(transaction["item"]["id"]))
        if not (sender and receiver and car):
            raise CommandErrorException("Invalid transaction, there was a problem with one or more of the details")
        # Add the transaction to the blockchain
        # Case invalid transaction
        if not self.server.blockchain.new_transaction(transaction):
            raise CommandErrorException("Transaction was failed")

        # Delete the car from the sender cars inventory
        if not await sender.remove_car(str(car.get_id())):
            raise CommandErrorException(f"Transaction was failed, couldn't find the car: {str(car)} in owner's inventory")
        # Transfer ownership of the car to the receiver
        car.set_owner(receiver.get_address(), receiver.access)
        await receiver.add_car(copy(car))

        # Create a transaction message and broadcast it to all connected users.
        transaction_message = create_transaction_message(self.server.external_ip, self.server.external_port,
                                                         transaction)
        message = BaseSchema().loads(transaction_message)
        await self.server.p2p_protocol.handle_message(message["message"])

        # If the number of pending transaction has reached the maximum, create a new block and store it.
        if self.server.blockchain.is_pending_transactions_full():
            # Try to add a new block containing all pending transactions to the blockchain
            if not self.server.blockchain.add_block(self.server.blockchain.new_block()):
                # If the block is not valid
                raise CommandErrorException("Fraudulent Block")
            # Broadcast a message to the server about the new block that was added to the blockchain
            await self.server.connection_pool.broadcast("A new Block was added to the blockchain")

    async def handle_transaction(self, transaction: TransactionSchema()) -> None:
        """
        Handles transaction command, a transaction made by a user, validates the transaction and adds it
        to the receivers pending transactions

        :param transaction: TransactionSchema, the transaction details.
        """
        # load sender receiver and car
        sender = self.server.connection_pool.get_authorized_user(transaction["sender"]["address"])
        receiver = self.server.connection_pool.get_authorized_user(transaction["receiver"]["address"])
        # loads the car from the server's car list
        car = self.server.cars.get_car(str(transaction["item"]["id"]))
        if not (sender and receiver and car):
            raise CommandErrorException("Invalid transaction, there was a problem with one or more of the details")

        # validate the transaction by sender's signature
        if not validate_transaction(transaction, sender):
            await self.server.connection_pool.broadcast("A fraudulent transaction was detected")
            return None

        # add the transaction to the receiver's pending transactions
        # TODO: get the car from the sender by the cars ID and do car.is_in_pending_transaction = true
        await receiver.add_pending_transaction(transaction)

    async def handle_new_car(self, car: dict[CarSchema]) -> None:
        """
        Handles new car command, a creation of a new car.

        :param car: CarSchema, dictionary that represents a car
        (accepted as dict and not as Car object in order to prevent aliasing
        in the server's inventory and the user's inventory)
        """
        car_obj = Car(**car)
        # Add the car to the server's car inventory
        self.server.cars.add_car(car_obj)
        # Broadcast a message to all connected users about the new car.
        await self.server.connection_pool.broadcast(f"A new car was created:\r\n{str(car_obj)}")

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
        await self.server.connection_pool.broadcast(f"A car was destroyed:\r\n{str(car)}")

    async def handle_success(self, _) -> None:
        """
        Handles an action on the server that doesn't require performing more actions
        :return: None
        """
        pass
