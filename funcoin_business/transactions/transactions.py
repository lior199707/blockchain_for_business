import json
from time import time

from nacl.exceptions import BadSignatureError

from funcoin_business.schema import CarSchema
from funcoin_business.cars.car import Car
from nacl.signing import VerifyKey
from nacl.encoding import HexEncoder

from funcoin_business.users.authorized_user import AuthorizedUser


def create_transaction(sender: AuthorizedUser, receiver: AuthorizedUser, car: Car) -> dict:
    """

    :param sender: User(object), the sender of the transaction
    :param receiver:  User(object), the receiver of the transaction
    :param car: Car(object), the car being transferred
    :return: dict, representing the transaction(the dict is similar to TransactionSchema)
    """
    item = CarSchema().loads(CarSchema().dumps(car))
    tx = {
        "timestamp": int(time()),
        "sender": {"address": sender.get_address(), "access": sender.get_access()},
        "receiver": {"address": receiver.get_address(), "access": receiver.get_access()},
        "item": item,
    }
    tx_bytes = json.dumps(tx, sort_keys=True).encode("ascii")

    # Now add the signature to the original transaction
    tx["signature"] = sender.sign(tx_bytes)
    return tx


def validate_transaction(transaction: dict, sender: AuthorizedUser) -> bool:
    """
    verifies that a given transaction was sent from the sender by his signature

    :param transaction: the Transaction dict
    :param sender: the sender of the transaction
    :return: Boolean, True if valid False otherwise
    """
    # Copy the transaction
    tx = transaction.copy()

    # Strip the "signature" key from the tx
    signature = tx.pop("signature")
    signature_bytes = HexEncoder.decode(signature)

    tx_bytes = json.dumps(tx, sort_keys=True).encode("ascii")

    # Generate a verifying key from the public key
    verify_key = VerifyKey(sender.get_public_key(), encoder=HexEncoder)

    # Attempt to verify the signature
    try:
        verify_key.verify(tx_bytes, signature_bytes)
    except BadSignatureError:
        return False
    else:
        return True
