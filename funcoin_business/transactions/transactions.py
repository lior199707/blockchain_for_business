import json
from time import time

from nacl.exceptions import BadSignatureError

from funcoin_business.schema import CarSchema
from funcoin_business.cars.car import Car
from funcoin_business.users.user import User
from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder


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
    }
    tx_bytes = json.dumps(tx, sort_keys=True).encode("ascii")

    # Now add the signature to the original transaction
    tx["signature"] = sender.sign(tx_bytes)
    return tx
