import trio
from trio_websocket import serve_websocket, ConnectionClosed
from functools import partial
import json
import logging
from dataclasses import dataclass, asdict


logging.basicConfig(
        format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-4s [%(asctime)s]  %(message)s',
        level=logging.INFO,
        filename='server_logger.log'
    )

@dataclass
class Bus:
    busId: str
    lat: float
    lng: float
    route: int

@dataclass
class WindowBounds:
    def __init__(self, east_lng, north_lat, south_lat, west_lng):
        self.east_lng = east_lng
        self.north_lat = north_lat
        self.south_lat = south_lat
        self.west_lng = west_lng

    def is_inside(self, lat, lng):
        return self.south_lat <= lat <= self.north_lat and self.west_lng <= lng <= self.east_lng

    def update(self, bounds):
        self.south_lat = bounds['south_lat']
        self.north_lat = bounds['north_lat']
        self.west_lng = bounds['west_lng']
        self.east_lng = bounds['east_lng']

async def get_coordinates(request, buses_on_map):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            message = json.loads(message)
            bus = Bus(busId=message['busId'], lat=message['lat'], lng=message['lng'], route=message['route'])
            buses_on_map.append(bus)
            # await trio.sleep(1)
        except ConnectionClosed:
            break

async def talk_to_browser(request, buses_on_map):
    ws = await request.accept()

    message = await ws.get_message()
    message = json.loads(message)
    bounds = WindowBounds(
        south_lat=message['data']['south_lat'],
        north_lat=message['data']['north_lat'],
        west_lng=message['data']['west_lng'],
        east_lng=message['data']['east_lng'],
    )
    buses_in_bounds = []
    for bus in buses_on_map:
        if WindowBounds.is_inside(bounds, bus.lat, bus.lng):
            buses_in_bounds.append(asdict(bus))
            logging.info(message)
            logging.info(f'{len(buses_in_bounds)} buses inside bounds')

    response = {
        "msgType": "Buses",
        "buses": buses_in_bounds
    }
    print(response)
    await ws.send_message(json.dumps(response))




async def main():
    buses = []
    get_buses_coordinates = partial(get_coordinates, buses_on_map=buses)
    send_buses_coordinates_to_browser = partial(talk_to_browser, buses_on_map=buses)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, get_buses_coordinates, '127.0.0.1', 8080, None)
        nursery.start_soon(serve_websocket, send_buses_coordinates_to_browser, '127.0.0.1', 8000, None)


if __name__ == "__main__":
    trio.run(main)
