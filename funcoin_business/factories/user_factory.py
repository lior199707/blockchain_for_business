import asyncio

from funcoin_business.users.authorized_user import AuthorizedUser
from funcoin_business.users.user import User
from funcoin_business.users.manufacturer import Manufacturer
from funcoin_business.users.dealer import Dealer
from funcoin_business.users.leasing_company import LeasingCompany
from funcoin_business.users.lessee import Lessee
from funcoin_business.users.scrap_merchant import ScrapMerchant
from funcoin_business.schema import AddressSchema


class UserFactory:
    """
    Class UserFactory, responsible for creating user objects.
    """

    def __init__(self):
        self.authorization_list = {

            AuthorizedUser.dealer: Dealer,
            AuthorizedUser.lessee: Lessee,
            AuthorizedUser.leasing_company: LeasingCompany,
            AuthorizedUser.manufacturer: Manufacturer,
            AuthorizedUser.scrap_merchant: ScrapMerchant,
        }

    async def get_user(self,
                       access: str,
                       writer: asyncio.StreamWriter,
                       reader: asyncio.StreamReader,
                       amount: int,
                       miner: bool,
                       address: AddressSchema(),
                       ) -> User | Manufacturer | Dealer | LeasingCompany | Lessee | ScrapMerchant:
        """
        Returns a user object based on the access given

        :param access: str, the access of the user
        :param writer: asyncio.StreamWriter
        :param reader: asyncio.StreamReader
        :param amount:int, the amount of money the user has(currently not in use)
        :param miner: Bool, indicating if the user is a miner(currently not in use)
        :param address: Str, "ip:port" of the user
        :return: one of the user objects, based on the user access
        """
        ctor = self.authorization_list.get(access)
        if not ctor:
            return User(writer, reader, 100, False, address)
        return ctor(writer, reader, 100, False, address)
