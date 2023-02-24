# Blockchain For Business

Opens a telnet server using python.<br>
the server handles a car responsibility chain, each user is a part from the chain.<br> 
The data of the transactions on the server is being saved by blockchian technology which provides a mutual shared ledger between the chain's parts(the users).

## Description

* The project was made after the degree's second year and before the degree's third year.

Uses tenet and cmd to handle the connection to the server.<br> 
When a user is connecting to the server he should provide his IP and port by input (beacuse the connection is with telnet and multiple cmd windows the real ip and port can't be used)
and provide his access.<br>

![image](https://user-images.githubusercontent.com/40609600/221218433-d282976a-2095-42d4-ba64-ad9368ef23fa.png)

### Allowed User Accesses
* Manufacturer
* Dealer 
* Leasing Company
* Lessee 
* Scrap Merchant 
(Should be typed exactly like the above or the user will get a guest access, keep reading for more details about guest access).<br><br>

After a user chooses his access the server conducts a vote, all the connected users vote whether the user should be authorized with the access he chose, if more than half of the users approve him, the new user will join the server and will be presented with the following menu:

![image](https://user-images.githubusercontent.com/40609600/221221682-d26ef303-9856-4f51-8624-713b7b432b71.png)

### Accesses permissions.

* Guest
  The guest can only use the /info command to watch all the cars and their details (color, model, owner) in the server's shared ledger.<br>
  He is not allowed to have/own any cars or making transactions.
  
* Manufacturer
  The manufacturer can create new cars.<br> 
  He can make a pending transaction of a car to a dealer on the srver that should be authorized by said dealer.<br>
  He can watch his own inventory of cars.

* Dealer
  The dealer can make a pending transaction of a car to a leasing company on the srver that should be authorized by said leasing company.<br>
  He can watch his own inventory of cars.

* Leasing Company
  The leasing company can make a pending transaction of a car to a lessee on the srver that should be authorized by said lessee.<br>
  Can watch it's own inventory of cars.

* Lessee 
  The dealer can make a pending transaction of a car to a scrap merchant on the srver that should be authorized by said scrap merchant.<br>
  He can watch his own inventory of cars.
  
* Scrap Merchant
  The scrap merchant can destroy cars which will erase them from the server's inventory.<br>
  He can watch his own inventory of cars.
  
(All the transactions are being verified by a private key, public key and signature each user have using pynacl).

### The blockchain

The blockchain stores transactions, each transaction mainly stores a sender receiver and a car, the block is a dictionary and in order to verify blocks we use their hash and python marshmallow schemas.<br>

```python
class BlockSchema(Schema):
    """
    class BlockSchema(marshmallow.Schema)
    {
        "height": Int, block number.
        "address": AddressSchema, the address of the creator.
        "transaction": list of TransactionSchema, the transactions the block holds.
        "previous_hash": Str, the hash of the previous block .
        "hash": Str, the hash of the block.
        "timestamp": Float, the time the block was created.
    }
    """

    height = fields.Int(required=True)
    address = fields.Nested(AddressSchema(), required=True)
    transaction = fields.Nested(TransactionSchema(many=True), required=True)
    previous_hash = fields.Str(required=True)
    hash = fields.Str(required=True)
    timestamp = fields.Float(required=True)

    class Meta:
        ordered = True
        
    
    class TransactionSchema(Schema):
    """
      class TransactionSchema(marshmallow.Schema)
      {
          "timestamp": Int, the time the transaction was made
          "sender": Str, the sender of the transaction.
          "receiver": Str, the receiver of the transaction
          "item": CarSchema, the car that was transacted
          "signature": Str, the signature of the sender
      }
      """

    timestamp = fields.Int(required=True)
    sender = fields.Nested(OwnerSchema(), required=True)
    receiver = fields.Nested(OwnerSchema(), required=True)
    item = fields.Nested(CarSchema(), required=True)
    signature = fields.Str(required=True)

    class Meta:
        ordered = True
```




