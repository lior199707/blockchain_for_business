import asyncio

from funcoin_business.blockchain import Blockchain
from funcoin_business.server import Server
from funcoin_business.connections import ConnectionPool

# Instantiate the blockchain and our pool for "peers"
blockchain = Blockchain()
connection_pool = ConnectionPool()

# Instantiate the server
server = Server(blockchain, connection_pool)


async def main():
    # start the server
    await server.listen()

if __name__ == "__main__":
    asyncio.run(main())
