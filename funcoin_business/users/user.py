import asyncio

from funcoin_business.schema import AddressSchema
from funcoin_business.utils import get_clean_str


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

    def get_access(self) -> None | str:
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
        return get_clean_str(response.decode("utf8").strip())

    async def make_action(self, _) -> None:
        """
        :param _: Any, ignorable
        :raise: NotImplementedError
        """
        raise NotImplementedError
