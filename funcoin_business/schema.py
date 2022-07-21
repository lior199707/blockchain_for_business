from time import time

import funcoin_business.blockchain
from funcoin_business import models


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


class TransactionSchema(Schema):
    """
      class TransactionSchema(marshmallow.Schema)
      {
          "timestamp": Int, the time the transaction was made
          "sender": Str, the sender of the transaction.
          "receiver": Str, the receiver of the transaction
          "item": Str, the item that was transacted
          "signature": Str, the signature of the sender
      }
      """

    timestamp = fields.Int(required=True)
    sender = fields.Str(required=True)
    receiver = fields.Str(required=True)
    item = fields.Str(required=True)
    signature = fields.Str(required=True)

    class Meta:
        ordered = True

    """@post_load
    def make(self, data, **kwargs):
        return models.Transaction(**data)"""


class BlockSchema(Schema):
    height = fields.Int(required=True)
    address = fields.Nested(Address(), required=True)
    transaction = fields.Nested(TransactionSchema(), required=True)
    previous_hash = fields.Str(required=True)
    hash = fields.Str(required=True)
    timestamp = fields.Int(required=True)

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

    @post_load
    def make(self, data, **kwargs):
        return models.Block(**data)


class PeerSchema(Schema):
    address = fields.Nested(Address(), required=True)
    last_seen = fields.Int(missing=lambda: int(time()))

    class Meta:
        ordered = True


def main():
    address = {}
    address["ip"] = '12345'
    address["port"] = '8888'
    # address = {"ip": '12345', "port": 8888}
    u = Address().load(address)
    print(u)
    print(u["ip"])
    print((u["port"]))


# {"ip": '1234', "port": 8888}

if __name__ == '__main__':
    main()
