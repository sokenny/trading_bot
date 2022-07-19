import uuid

class Operation:
    def __init__(self, status, start_price, end_price, stop_loss, amount, type, weight, create_time, position_id, id=False):
        self.status = status
        self.start_price = round(start_price, 5)
        self.end_price = round(end_price, 5)
        self.stop_loss = round(stop_loss, 5)
        self.amount = amount
        self.type = type
        self.weight = weight
        self.create_time = create_time
        self.position_id = position_id

        self.id = id or str(uuid.uuid4())
        self.open_time = None
        self.close_time = None
        self.outcome = None
        self.open_price = None
        self.exit_price = None
        self.quantity = round(self.amount / self.start_price, 5)

    def get(self):
        return {'status': self.status, 'start_price': self.start_price, 'end_price': self.end_price, 'stop_loss': self.stop_loss, 'amount': self.amount, 'quantity':self.quantity, 'type': self.type, 'open_price': self.open_price, 'exit_price': self.exit_price, 'weight': self.weight, 'create_time': self.create_time,  'open_time': self.open_time, 'close_time': self.close_time, 'outcome': self.outcome, 'position_id': self.position_id, 'id': self.id}
