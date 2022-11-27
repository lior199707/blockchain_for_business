import funcoin_business.users.user
from funcoin_business.cars.car import Car


class NoCarsException(Exception):
    pass


class CarInventory:
    """
    Class CarInventory, handles a collection of cars.
    """

    def __init__(self):
        # Inventory: {"car_id": car_obj}
        self.inventory = {}

    def add_car(self, car: Car) -> None:
        """
        Adds a car to the inventory
        :param car: Car, the car to add to the inventory
        """
        self.inventory[str(car.get_id())] = car

    async def remove_car(self, car_id: str) -> bool:
        """
        Removes a car from the inventory
        :param car_id: Str, the id of the car to remove from the inventory
        :return: Bool, True if succeeded, False otherwise
        """
        try:
            self.inventory.pop(car_id)
            return True
        except KeyError:
            return False

    def get_car(self, car_id: str) -> Car | None:
        """
        Gets a car from the inventory
        :param car_id: Str, the id of the wanted car
        :return: Car, if the inventory hold a car with a matching id, None otherwise
        """
        return self.inventory.get(car_id)

    def view_cars(self) -> str:
        """
        :raises: NoCarsException - if there are no cars in the inventory
        :return: Str, containing all the cars in the inventory
        """
        if not self.has_cars():
            raise NoCarsException("There are no cars in the inventory")
        return str(self)

    def has_cars(self) -> bool:
        """
        :return: Bool, True if there are cars in the inventory, False otherwise
        """
        return len(self.inventory) > 0

    def __str__(self):
        message = ""
        for car in list(self.inventory.values()):
            message += str(car)
        return message
