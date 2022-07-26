from time import time

import funcoin_business.blockchain

from marshmallow import Schema, fields, validates_schema, ValidationError, post_load
from marshmallow.exceptions import MarshmallowError


class AddressSchema(Schema):
    """
    class AddressSchema(marshmallow.Schema)
    {
        "ip": Str, user ip
        "port": Int, the port the user is listening on
    }
    """

    ip = fields.Str(required=True)
    port = fields.Int(required=True)

    class Meta:
        ordered = True


class OwnerSchema(Schema):
    """
    class OwnerSchema(marshmallow.Schema)

    {
        address: str, "ip:port" of the owner
        access: str, the access of the owner
    }
    """
    address = fields.Str(required=True)
    access = fields.Str(required=True)

    class Meta:
        ordered = True


class CarSchema(Schema):
    """
    class CarSchema(marshmallow.Schema)
    {
        "id": int, identification number of the car(should be unique).
        "owner": OwnerSchema
        {
            address: str, ip:port of the owner
            access: str, the access of the owner
        }
        model: str, the model of the car
        color: str, the model of the car
    }
    """
    id = fields.Int(required=True)
    owner = fields.Nested(OwnerSchema(), required=True)
    model = fields.Str(required=True)
    color = fields.Str(required=True)

    class Meta:
        ordered = True


class TransactionSchema(Schema):
    """
      class TransactionSchema(marshmallow.Schema)
      {
          "timestamp": Int, the time the transaction was made
          "sender": Str, the sender of the transaction.
          "receiver": Str, the receiver of the transaction
          "item": CarSchema, the car that was transacted
          "signature": Str, the signature of the sender
      }
      """

    timestamp = fields.Int(required=True)
    sender = fields.Nested(OwnerSchema(), required=True)
    receiver = fields.Nested(OwnerSchema(), required=True)
    item = fields.Nested(CarSchema(), required=True)
    signature = fields.Str(required=True)

    class Meta:
        ordered = True


class BlockSchema(Schema):
    """
    class BlockSchema(marshmallow.Schema)
    {
        "height": Int, block number.
        "address": AddressSchema, the address of the creator.
        "transaction": list of TransactionSchema, the transactions the block holds.
        "previous_hash": Str, the hash of the previous block .
        "hash": Str, the hash of the block.
        "timestamp": Float, the time the block was created.
    }
    """

    height = fields.Int(required=True)
    address = fields.Nested(AddressSchema(), required=True)
    transaction = fields.Nested(TransactionSchema(many=True), required=True)
    previous_hash = fields.Str(required=True)
    hash = fields.Str(required=True)
    timestamp = fields.Float(required=True)

    class Meta:
        ordered = True

    # a special decorator indicating that Marshmallow should run ths function as part of its validation process.
    @validates_schema
    def validate_hash(self, data, **kwargs):
        """
        validates a transaction at the point of deserialization to ensure that any transaction is always valid.
        if the transaction is not valid raising Marshmallow.ValidationError(Exception).
        """
        block = data.copy()
        # Remove the hash key and its matching value
        block.pop("hash")

        # if the hash of the block doesn't match the hash provided.
        if data["hash"] != funcoin_business.blockchain.Blockchain.hash(block):
            raise ValidationError("Fraudulent block: hash is wrong")


class PeerSchema(Schema):
    """
    class PeerSchema(marshmallow.Schema)
    {
        "address": AddressSchema, the address of the peer.
        "last_seen": Int, last time the peer was seen on the network.
    }
    """
    address = fields.Nested(AddressSchema(), required=True)
    last_seen = fields.Int(missing=lambda: int(time()))

    class Meta:
        ordered = True
