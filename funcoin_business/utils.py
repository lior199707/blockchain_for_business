import asyncio
import socket


# TODO: make the functions static in the User class
async def get_fake_ip_and_port(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> tuple:
    """
    Gets user's IP and port as input, IP should be a String, port should be an integer.

    :param reader: asyncio.StreamReader
    :param writer: asyncio.StreamWriter
    :return: Tuple (IP, port)
    """
    writer.write("> Please enter your ip: ".encode())
    ip = await reader.readuntil(b"\n")
    decoded_ip = ip.decode("utf8").strip()
    writer.write("> Please enter your port: ".encode())
    port = await reader.readuntil(b"\n")
    decoded_port = port.decode("utf8").strip()
    return decoded_ip, decoded_port


async def get_ip_and_port() -> tuple:
    """
    Opens a socket and gets user's IP and port.

    :return: Tuple (IP, port) of the user
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        address = s.getsockname()
        IP = address[0]
        port = address[1]
    except Exception:
        IP = '127.0.0.1'
        port = '8888'
    finally:
        s.close()
    return IP, port
