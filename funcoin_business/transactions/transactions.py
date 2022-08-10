
from time import time

from funcoin_business.schema import CarSchema
from funcoin_business.cars.car import Car
from funcoin_business.users.user import User


def create_transaction(sender: User, receiver: User, car: Car) -> dict:
    """

    :param sender: User(object), the sender of the transaction
    :param receiver:  User(object), the receiver of the transaction
    :param car: Car(object), the car being transferred
    :return: dict, representing the transaction(the dict is similar to TransactionSchema)
    """
    item = CarSchema().loads(CarSchema().dumps(car))
    tx = {
        "timestamp": int(time()),
        "sender": sender.get_address(),
        "receiver": receiver.get_address(),
        "item": item,
        "signature": "some signature"
    }
    return tx
