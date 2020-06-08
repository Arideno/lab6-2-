from abc import ABC
from typing import List, Dict
import subprocess as sp
from enum import Enum


class Broker:
    def __init__(self, name, congestion=0):
        self.name = name
        self.congestion = congestion

    def __repr__(self):
        return f'{self.name} {self._congestion}'

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError
        self._name = value

    @property
    def congestion(self):
        return self._congestion

    @congestion.setter
    def congestion(self, value):
        if not isinstance(value, int):
            raise ValueError
        self._congestion = value


class Client(ABC):
    def __init__(self, name, phone):
        self.name = name
        self.phone = phone

    def __repr__(self):
        return f'{self.name}({self.phone})'

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError
        self._name = value

    @property
    def phone(self):
        return self._phone

    @phone.setter
    def phone(self, value):
        if not isinstance(value, str):
            raise ValueError
        self._phone = value

    def __hash__(self):
        return hash(self.phone)


class Buyer(Client):
    pass


class Seller(Client):
    def __init__(self, name, phone):
        super(Seller, self).__init__(name, phone)
        self._apartments = []

    @property
    def apartments(self) -> List:
        return self._apartments

    def add_apartment(self, apartment):
        if not isinstance(apartment, Apartment):
            raise ValueError
        self._apartments.append(apartment)


class DealStatus(Enum):
    FAILED = 1
    DONE = 2


class Apartment:
    def __init__(self, address, area, num_rooms, client: Seller):
        self.address = address
        self.client = client
        self.client.add_apartment(self)
        self.area = area
        self.num_rooms = num_rooms

    def __repr__(self):
        return f'Address: {self.address}, Area: {self.area} Number of rooms: {self.num_rooms}'

    @property
    def address(self):
        return self._address

    @address.setter
    def address(self, value):
        if not isinstance(value, str):
            raise ValueError
        self._address = value

    @property
    def area(self):
        return self._area

    @area.setter
    def area(self, value):
        if not isinstance(value, float):
            raise ValueError
        self._area = value

    @property
    def num_rooms(self):
        return self._num_rooms

    @num_rooms.setter
    def num_rooms(self, value):
        if not isinstance(value, int):
            raise ValueError
        self._num_rooms = value

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        if not isinstance(value, Seller):
            raise ValueError
        self._client = value


class Deal(ABC):
    def __init__(self, apartment: Apartment, time: str, broker: Broker, status=DealStatus.FAILED):
        self.apartment = apartment
        self.time = time
        self.status = status
        self.broker = broker


class SaleDeal(Deal):
    pass


class BuyDeal(Deal):
    pass


class Firm:
    def __init__(self, name: str):
        self.name = name
        self.brokers = []
        self.clients = []
        self.deals = []
        self._division: Dict[Client, Broker] = dict()
        self.file_name = name.lower().replace(' ', '')
        try:
            self.file = open(f'./data/{self.file_name}.csv', 'r+')
            print('Database loaded!')
        except:
            open(f'./data/{self.file_name}.csv', 'w').close()
            self.file = open(f'./data/{self.file_name}.csv', 'r+')
        for line in self.file.readlines():
            data = line.split(',')
            if data[0] == '0':
                self.brokers.append(Broker(data[1], int(data[2])))
            elif data[0] == '1':
                c = Seller(data[1], data[2].rstrip())
                broker = None
                for br in self.brokers:
                    if br.name == data[3].rstrip():
                        broker = br
                        break
                if broker is None:
                    continue
                self._division[c] = broker
                self.clients.append(c)
            elif data[0] == '2':
                c = Buyer(data[1], data[2].rstrip())
                broker = None
                for br in self.brokers:
                    if br.name == data[3].rstrip():
                        broker = br
                        break
                if broker is None:
                    continue
                self._division[c] = broker
                self.clients.append(c)
            elif data[0] == '3':
                s = None
                for client in [x for x in self.clients if isinstance(x, Seller)]:
                    if client.phone == data[4].rstrip():
                        s = client
                        break
                if s is None:
                    continue
                _ = Apartment(data[1], float(data[2]), int(data[3]), s)
            elif data[0] == '4':
                a = None
                for client in [x for x in self.clients if isinstance(x, Seller)]:
                    for apartment in client.apartments:
                        if data[1] == apartment.address:
                            a = apartment
                            break
                if a is None:
                    continue
                b = None
                for broker in self.brokers:
                    if broker.name == data[3]:
                        b = broker
                        break
                if b is None:
                    continue
                deal = SaleDeal(a, data[4].rstrip(), b, DealStatus(int(data[2])))
                self.deals.append(deal)
            elif data[0] == '5':
                a = None
                for client in [x for x in self.clients if isinstance(x, Seller)]:
                    for apartment in client.apartments:
                        if data[1] == apartment.address:
                            a = apartment
                            break
                if a is None:
                    continue
                b = None
                for broker in self.brokers:
                    if broker.name == data[3]:
                        b = broker
                        break
                if b is None:
                    continue
                deal = BuyDeal(a, data[4].rstrip(), b, DealStatus(int(data[2])))
                self.deals.append(deal)
        self.file.close()
        self.file = open(f'./data/{self.file_name}.csv', 'w')

    def __del__(self):
        for broker in self.brokers:
            self.file.write(f'0,{broker.name},{broker.congestion}\n')
        for client in [x for x in self.clients if isinstance(x, Seller)]:
            self.file.write(f'1,{client.name},{client.phone},{self._division[client].name}\n')
        for client in [x for x in self.clients if isinstance(x, Buyer)]:
            self.file.write(f'2,{client.name},{client.phone},{self._division[client].name}\n')
        for client in [x for x in self.clients if isinstance(x, Seller)]:
            for apartment in client.apartments:
                self.file.write(
                    f'3,{apartment.address},{apartment.area},{apartment.num_rooms},{apartment.client.phone}\n')
        for deal in [x for x in self.deals if isinstance(x, SaleDeal)]:
            self.file.write(f'4,{deal.apartment.address},{deal.status.value},{deal.broker.name},{deal.time}\n')
        for deal in [x for x in self.deals if isinstance(x, BuyDeal)]:
            self.file.write(f'5,{deal.apartment.address},{deal.status.value},{deal.broker.name},{deal.time}\n')
        self.file.close()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise ValueError
        self._name = value

    @property
    def brokers(self) -> List[Broker]:
        return self._brokers

    @brokers.setter
    def brokers(self, value: List[Broker]):
        if not isinstance(value, list):
            raise ValueError
        if len(value) != 0 and not any(isinstance(x, Broker) for x in value):
            raise ValueError
        self._brokers = value

    @property
    def clients(self) -> List[Client]:
        return self._clients

    @clients.setter
    def clients(self, value: List[Client]):
        if not isinstance(value, list):
            raise ValueError
        if len(value) != 0 and not any(isinstance(x, Client) for x in value):
            raise ValueError
        self._clients = value

    @property
    def deals(self) -> List[Deal]:
        return self._deals

    @deals.setter
    def deals(self, value: List[Deal]):
        if not isinstance(value, list):
            raise ValueError
        if len(value) != 0 and not any(isinstance(x, Deal) for x in value):
            raise ValueError
        self._deals = value

    def add_broker(self, broker: Broker):
        if not isinstance(broker, Broker):
            raise ValueError
        self.brokers.append(broker)

    def add_client(self, client: Client):
        if not isinstance(client, Client):
            raise ValueError
        if client in self.clients:
            raise ValueError
        if len(self.brokers) == 0:
            input('No brokers!')
            return
        self.clients.append(client)
        broker = min(self.brokers, key=lambda br: br.congestion)
        self._division[client] = broker
        broker.congestion += 1

    def request(self, apartment: Apartment):
        print(f'Broker {self._division[apartment.client]} is calling {apartment.client}.')
        time = input('Enter negotiation\'s time: ')
        a = input('Accept deal?(1 - YES): ')
        deal = SaleDeal(apartment, time, self._division[apartment.client])
        if a == '1':
            deal.status = DealStatus.DONE
        self.deals.append(deal)
        print('Deal Created!')

    def buy(self, buyer: Buyer, apartment: Apartment):
        print(f'{buyer} wants to buy apartment {apartment}')
        print(f'Broker {self._division[buyer]} is calling {apartment.client}.')
        time = input('Enter negotiation\'s time: ')
        a = input('Accept deal?(1 - YES): ')
        deal = BuyDeal(apartment, time, self._division[buyer])
        if a == '1':
            deal.status = DealStatus.DONE
        self.deals.append(deal)
        print('Deal Created!')


if __name__ == '__main__':
    print('Мойсол Андрiй Олексiйович, IП-96, 14 варiант')
    firm_name = input('Enter firm name: ')
    firm = Firm(firm_name)

    while True:
        sp.call('clear', shell=True)
        print('Мойсол Андрiй Олексiйович, IП-96, 14 варiант')
        action = input('Enter action(0-exit, 1-create broker, 2-create seller, 3-create buyer, 4-add apartment, '
                       '5-buy apartment, 6-get broker\'s deals info)')
        if action == '0':
            del firm
            break
        elif action == '1':
            name = input('Enter broker\'s name: ')
            congestion = int(input('Enter broker\'s congestion: '))
            firm.add_broker(Broker(name, congestion))
        elif action == '2':
            name = input('Enter seller\'s name: ')
            phone = input('Enter seller\'s phone: ')
            firm.add_client(Seller(name, phone))
        elif action == '3':
            name = input('Enter buyer\'s name: ')
            phone = input('Enter buyer\'s phone: ')
            firm.add_client(Buyer(name, phone))
        elif action == '4':
            sellers = []
            for client in [x for x in firm.clients if isinstance(x, Seller)]:
                sellers.append(client)
            for i in range(len(sellers)):
                print(f'{i}. {sellers[i]}')
            if len(sellers) == 0:
                input('No sellers!')
                continue
            num = int(input('Select seller: '))
            seller = sellers[num]
            address = input('Enter address of apartment: ')
            area = float(input('Enter area: '))
            num_rooms = int(input('Enter number of rooms: '))
            apartment = Apartment(address, area, num_rooms, seller)
            firm.request(apartment)
            input()
        elif action == '5':
            buyers = []
            for client in [x for x in firm.clients if isinstance(x, Buyer)]:
                buyers.append(client)
            for i in range(len(buyers)):
                print(f'{i}. {buyers[i]}')
            if len(buyers) == 0:
                input('No buyers!')
                continue
            num = int(input('Select buyer: '))
            buyer = buyers[num]
            apartments = []
            for client in [x for x in firm.clients if isinstance(x, Seller)]:
                apartments.extend(client.apartments)
            for i in range(len(apartments)):
                print(f'{i}. {apartments[i]}')
            if len(apartments) == 0:
                input('No apartments')
            else:
                num = int(input('Select apartment: '))
                apartment = apartments[num]
                firm.buy(buyer, apartment)
                input()
        elif action == '6':
            for i in range(len(firm.brokers)):
                print(f'{i}. {firm.brokers[i].name}')
            if len(firm.brokers) == 0:
                print('No brokers!')
            else:
                num = int(input('Select broker'))
                broker = firm.brokers[num]
                num_deals = 0
                num_successful_deals = 0
                for deal in firm.deals:
                    if deal.broker == broker:
                        num_deals += 1
                        if deal.status == DealStatus.DONE:
                            num_successful_deals += 1
                print(f'Number of deals: {num_deals}\nNumber of successful deals: {num_successful_deals}')
                input()
