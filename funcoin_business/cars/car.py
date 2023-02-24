class Car:
    """
    Class Car, handles cars.
    """

    def __init__(self, id: int, owner: dict, model: str, color: str):
        """
        instantiates a Car.

        :param: ID: int, a unique number
        :param owner: dict, {address: str (ip:port) , access: str}
        :param model: str, the brand of the car
        :param color: str, the color of the car
        """
        self.id = id
        self.owner = owner
        self.model = model
        self.color = color

        # TODO: add a bool var indicating if a car is in a pending transaction, init value is false

    def get_id(self) -> int:
        """
        :return: int, the ID of the car
        """
        return self.id

    def get_owner_address(self) -> str:
        """
        :return: str, "ip:port" of the owner
        """
        return self.owner["address"]

    def get_owner_access(self) -> str:
        """
        :return: str, the owner access in the blockchain, his role
        """
        return self.owner["access"]

    def get_model(self) -> str:
        """
        :return: str, the model/brand of the car
        """
        return self.model

    def get_color(self) -> str:
        """
        :return: str, the color of the car
        """
        return self.color

    # TODO: method that returns bool if the car is in_pending_tranasction

    def set_owner(self, address: str, access: str) -> None:
        """
        sets the owner of the car.
        :param address: str, "ip:port" of the new owner
        :param access: str, the access of the new owner
        """
        self.owner["address"] = address
        self.owner["access"] = access

    def __str__(self):
        return f"Car:\r\n" \
               f"  id: {self.get_id()}\r\n" \
               f"  model: {self.get_model()}\r\n"\
               f"  color: {self.get_color()}\r\n"\
               f"  Owner:\r\n" \
               f"    address: {self.get_owner_address()}\r\n" \
               f"    access: {self.get_owner_access()}\r\n"

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)
        return result






# Car {"ID": int (key of dict), "owner": {address: (ip:port) str, access: str} "model": str, color: str}
