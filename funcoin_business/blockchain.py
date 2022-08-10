import asyncio
import json
import math
import random
from hashlib import sha256
from time import time
import structlog
from marshmallow.exceptions import MarshmallowError

from funcoin_business.schema import TransactionSchema, BlockSchema


logger = structlog.getLogger("blockchain")


class Blockchain(object):
    """
    class Blockchain handles a blockchain
    """
    Max_Transactions = 2

    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        # create the genesis block
        logger.info("creating genesis block")
        self.chain.append(self.new_block())

    def new_block(self):
        """
        creates a new block.

        :return: the block.
        """
        # Generates a new block
        block = self.create_block(
            height=len(self.chain),
            address={"ip": "0.0.0.0", "port": 8888},
            transactions=self.pending_transactions,
            previous_hash=self.last_block['hash'] if self.last_block else "first block",
            timestamp=time(),
        )

        # Reset the list of pending transactions
        self.pending_transactions = []
        return block

    @staticmethod
    def hash(block: dict):
        """
        gets a block and returns its hash calculates by sha256.

        :param block: the block to generate it hash.
        :return:
        """
        # Hashes a block
        # We ensure the dictionary is sorted, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return sha256(block_string).hexdigest()

    @staticmethod
    def create_block(height: int,
                     address: dict,
                     transactions: list[TransactionSchema],
                     previous_hash: str,
                     timestamp: float = None,
                     ) -> dict:
        """
        creates a new block.

        :param height: the index of the block
        :param address: dict, ip and port of the creator.
        :param transactions: the transactions stored in the block
        :param previous_hash: the hash of the previous block in the chain
        :param timestamp: float, the time the block was created on
        :return: dictionary representing a block(similar to BlockSchema).
        """
        block = {"height": height,
                 "address": address,
                 "transaction": transactions,
                 "previous_hash": previous_hash,
                 "timestamp": timestamp or time(),
                 }
        # Get the hash of the new block, and add it to the block
        block["hash"] = Blockchain.hash(block)
        print("Added Block:::::::::::::::::::", block)
        return block

    @property
    def last_block(self):
        """
        Returns the last block in the chain (if there are blocks)

        :return: the last block if exists, otherwise None.
        """
        return self.chain[-1] if self.chain else None

    def add_block(self, block: dict) -> bool:
        """
        gets a block and add it to the chain

        :param block: , dict representing the block to add
        :return: Boolean, True if added the block successfully, False otherwise
        """
        # Verify the block
        try:
            verified_block = BlockSchema().load(block)
        except (MarshmallowError, json.decoder.JSONDecodeError) as e:
            print(e)
            return False
        self.chain.append(verified_block)
        return True

    async def get_blocks_after_timestamp(self, timestamp: float) -> list[dict]:
        """

        :param timestamp: float value representing the timestamp
        :return: a list of all the blocks whose timestamps are bigger than the timestamp received.
        The list containing dictionary of type BlockSchema
        """
        for index, block in enumerate(self.chain):
            if timestamp < block["timestamp"]:
                return self.chain[index:]

    def new_transaction(self, transaction: dict) -> None:
        """
        Adds a new transaction to the list of pending transactions.

        :param transaction: TransactionSchema, dict with all the transaction details
        """
        # Validate the transaction
        try:
            tx = TransactionSchema().load(transaction)
        except (MarshmallowError, json.decoder.JSONDecodeError):
            print("Error, invalid transaction")
            return None

        # Add the transaction to the list of pending transaction
        self.pending_transactions.append(tx)
        print("pending transactions::::::::::::::::::::::", self.pending_transactions)

        # If the number of pending transation has reached the maximum, create a new block and store it.
        if len(self.pending_transactions) == 2:
            print("amount of transactions is 2 so creating a new block")
            self.add_block(self.new_block())
