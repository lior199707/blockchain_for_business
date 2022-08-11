import asyncio
from funcoin_business.cars.car_inventory import CarInventory
from funcoin_business.schema import AddressSchema
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder


class User:
    """
    Class User , handles users with no access(guests), means they can't perform any transactions
    nor actions, have only read access(can only view information on the server)
    """

    def __init__(self,
                 writer: asyncio.StreamWriter,
                 reader: asyncio.StreamReader,
                 amount: float,
                 miner: bool,
                 address: AddressSchema,
                 ):
        """
        :param writer: asyncio.StreamWriter
        :param reader: asyncio.StreamReader
        :param amount: float, the amount of money
        :param miner: bool, indicates if the user is a miner
        :param address: dict(schema.AddressSchema), {"ip": ip, "port": port}
        """
        self.writer = writer
        self.reader = reader
        self.amount = amount
        self.miner = miner
        self.address = address
        self.access = None
        self.cars = CarInventory()
        self.private_key = SigningKey.generate()

    @property
    async def get_next_in_chain(self):
        """
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def get_writer(self) -> asyncio.StreamWriter:
        """
        :return:asyncio.StreamWriter, the writer of the user
        """
        return self.writer

    def get_reader(self) -> asyncio.StreamReader:
        """
        :return: asyncio.StreamReader, the reader of the user
        """
        return self.reader

    def is_miner(self) -> bool:
        """
        :return:boolean, true if the user is a miner, false otherwise
        """
        return self.miner

    def get_ip(self) -> str:
        """
        :return:str, the ip of the user
        """
        return self.address["ip"]

    def get_port(self) -> int:
        """
        :return:int, the port of the user
        """
        return self.address["port"]

    def get_address(self) -> str:
        """
        :return:String, "ip:port" of the user
        """
        return f'{self.get_ip()}:{self.get_port()}'

    def get_access(self) -> None:
        """
        :return: None, guest has no access
        """
        return self.access

    async def receive_message(self, message: str) -> None:
        """
        sending a message to the user using asyncio.StreamWriter
        :param message: the message to receive
        """
        self.writer.write(f'{message}\r\n'.encode())

    async def respond(self) -> str:
        """
        Gets keyboard input from the user
        :return: Str, user's input
        """
        response = await self.reader.readuntil(b"\n")
        return response.decode("utf8").strip()

    async def make_action(self, _) -> None:
        """
        :param _: Any, ignorable
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def get_public_key(self) -> bytes:
        """
        :return: <bytes>, encoded verification key of the user, used to verify the user's signatures
        """
        return self.private_key.verify_key.encode(encoder=HexEncoder)

    def sign(self, data: bytes) -> str:
        """
        Lets the user sign on transactions.

        :param data: bytes, the data to sign on
        :return: str, representing the encoded signature of the user
        """
        signature = self.private_key.sign(data).signature
        return HexEncoder.encode(signature).decode("ascii")
