from marshmallow import Schema, fields, post_load
from marshmallow_oneofschema import OneOfSchema

from funcoin_business import schema


class PeerMessage(Schema):
    """
    class PeerMessage(marshmallow.Schema)
    {
        "payload": schema.PeerSchema, the peer joining the network
        "name": Str, the name of the message initialized automatically to "peer".
    }
    """
    payload = fields.Nested(schema.PeerSchema())

    @post_load
    def add_name(self, data, **kwargs):
        # indicating it's a peer message for identification.
        data["name"] = "peer"
        return data


class BlockMessage(Schema):
    """
    class BlockMessage(marshmallow.Schema)
    {
        "payload": schema.BlockSchema, the block.
        "name": Str, the name of the message initialized automatically to "block".
    }
    """

    payload = fields.Nested(schema.BlockSchema())

    @post_load
    def add_name(self, data, **kwargs):
        # indicating it's a peer message for identification.
        data["name"] = "block"
        return data


class TransactionMessage(Schema):
    """
    class TransactionMessage(marshmallow.Schema)
    {
        "payload": schema.TransactionSchema, the transaction.
        "name": Str, the name of the message initialized automatically to "transaction".
    }
    """

    payload = fields.Nested(schema.TransactionSchema())

    @post_load
    def add_name(self, data, **kwargs):
        # indicating it's a peer message for identification.
        data["name"] = "transaction"
        return data


class MessageDisambiguation(OneOfSchema):
    """
    Schemas handler, uses the name of the message to load the right schema.
    """

    type_field = "name"
    type_schemas = {
        "peer": PeerMessage,
        "block": BlockMessage,
        "transaction": TransactionMessage,
    }

    def get_obj_type(self, obj):
        if isinstance(obj, dict):
            return obj.get("name")


class MetaSchema(Schema):
    """
    class MetaSchema(marshmallow.Schema)
    {
        "address": schema.AddressSchema, public ip and port of the server.
        "client": Str, the version of the software.
    }
    """

    address = fields.Nested(schema.AddressSchema())
    client = fields.Str()


class BaseSchema(Schema):
    """
    class BaseSchema(marshmallow.Schema)
    {
        "meta": MetaSchema.
        "message": MessageDisambiguation, one of the allowed message schemas:
                    (PeerMessage, BlockMessage, TransactionMessage).
    }
    """

    meta = fields.Nested(MetaSchema())
    message = fields.Nested(MessageDisambiguation())


def meta(ip, port, version="funcoin-0.1"):
    """

    :param ip: the public IP of the peer
    :param port: the port the peer is listening on
    :param version: the version
    :return: dictionary containing 2 keys, "client", "address"
    address is also a dictionary of 2 keys: "ip", "port".
    """
    return {
        "address": {"ip": ip, "port": port},
        "client": version,
    }


def create_peers_message(external_ip: str, external_port: int, peer: schema.PeerSchema):
    """
    Generates a message containing a Peer, should be used when an authorized user is joining the server.

    :param external_ip: the public IP of the peer
    :param external_port: the port the peer is listening on
    :param peer: PeerSchema.
    :return: JSON encoded string of the transaction message.
    """
    return BaseSchema().dumps(
        {
            "meta": meta(external_ip, external_port),
            "message": {"name": "peer", "payload": peer},
        }
    )


def create_block_message(external_ip, external_port, block):
    """
    Generates a message containing a block.

    :param external_ip: the public IP of the peer
    :param external_port: the port the peer is listening on
    :param block: block payload,a dictionary.
    :return: JSON encoded string of the transaction message.
    """
    return BaseSchema().dumps(
        {
            "meta": meta(external_ip, external_port),
            "message": {"name": "block", "payload": block},
        }
    )


def create_transaction_message(external_ip, external_port, tx):
    """
    Generates a message containing a transaction.

    :param external_ip: the public IP of the peer
    :param external_port: the port the peer is listening on
    :param tx: transaction payload, a dictionary.
    :return: JSON encoded string of the block message.
    """
    return BaseSchema().dumps(
        {
            "meta": meta(external_ip, external_port),
            "message": {
                "name": "transaction",
                "payload": tx,
            },
        }
    )

