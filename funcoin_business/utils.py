import asyncio
import socket
import aiohttp


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


async def get_external_ip():
    """
    :return: the external ip of the user.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get('http://ipinfo.io', headers={"user-agent": "curl/7.64.1"}) as response:
            response_json = await response.json(content_type=None)
            ip = response_json["ip"]
            return ip


def get_clean_str(string: str):
    # find the first appearance of the backspace
    backspace_index = string.find('\b')
    # as long as the string contains a backspace char
    while backspace_index != -1:
        # if there is a letter before the backspace
        if backspace_index != 0:
            # copy all the string except the backspace and the deleted char
            string = string[:backspace_index - 1] + string[backspace_index + 1:]
        # else, copy all the string except the backspace
        else:
            string = string[:backspace_index] + string[backspace_index + 1:]

        backspace_index = string.find('\b')
    return string
