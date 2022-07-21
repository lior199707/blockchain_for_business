from time import time


class Address:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    def __eq__(self, other):
        if isinstance(other, Address):
            return self.ip == other.ip and self.port == other.port


class Block:
    def __init__(self, height, address, transaction, previous_hash, hash, timestamp):
        self.height = height
        # the address {ip, port} of the creator
        self.address = address
        self.transaction = transaction
        self.previous_hash = previous_hash
        self.hash = hash
        self.timestamp = timestamp

    def __eq__(self, other):
        if isinstance(other, Block):
            return (self.height == other.height and
                    self.address == other.address and
                    self.transaction == other.transaction and
                    self.previous_hash == other.previous_hash and
                    self.hash == other.hash and
                    self.timestamp == other.timestamp
                    )
        return False


class Transaction:
    def __init__(self, timestamp, sender, receiver, item, signature):
        self.timestamp = timestamp
        self.sender = sender
        self.receiver = receiver
        self.item = item
        self.signature = signature

    def __eq__(self, other):
        if isinstance(other, Transaction):
            return (self.timestamp == other.timestamp and
                    self.sender == other.sender and
                    self.receiver == other.receiver and
                    self.item == other.item and
                    self.signature == other.signature
                    )
        return False


class Peer:
    def __init__(self, address, last_seen):
        self.address = address
        self.last_seen = last_seen

    def __eq__(self, other):
        if isinstance(other, Peer):
            return self.address == other.address and self.last_seen == other.last_seen
        return False
