import asyncio


class User:

    """
    Handles users joining to the server
    """
    def __init__(self,
                 writer: asyncio.StreamWriter,
                 reader: asyncio.StreamReader,
                 amount: float,
                 miner: bool,
                 address: dict,
                 ):
        self.writer = writer
        self.reader = reader
        self.amount = amount
        self.is_miner = miner
        self.address = address

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

        return self.is_miner

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

        :return:String, ip:port of the user
        """
        return f'{self.get_ip()}:{self.get_port()}'

    async def receive_message(self, message: str) -> None:
        """
        sending a message to the user using asyncio.StreamWriter
        :param message: the message to receive
        """
        self.writer.write(f'{message}\r\n'.encode())

    async def respond(self):
        response = await self.reader.readuntil(b"\n")
        return response.decode("utf8").strip()
