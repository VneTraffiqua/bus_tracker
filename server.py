import contextlib
import trio
from trio_websocket import serve_websocket, ConnectionClosed
from functools import partial
import json
import logging
import click
from dataclasses import dataclass, asdict


def setup_logging(debug):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-4s [%(asctime)s]  %(message)s',
        level=level,
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
    def __init__(self):
        self.east_lng = None
        self.north_lat = None
        self.south_lat = None
        self.west_lng = None

    def is_inside(self, lat, lng):
        if self.south_lat and self.north_lat and self.west_lng and self.east_lng:
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
        except json.JSONDecodeError:
            response = {
                "errors": ["Requires valid JSON"],
                "msgType": "Errors"
            }
            logging.info(response)
            await ws.send_message(json.dumps(response))
            continue
        except KeyError:
            response = {
                "errors": ["Requires valid JSON"],
                "msgType": "Errors"
            }
            logging.info(response)
            await ws.send_message(json.dumps(response))
            continue
        except ConnectionClosed:
            break

async def listen_browser(ws ,bounds):
    while True:
        try:
            message = await ws.get_message()
            logging.info(message)
            if 'msgType' not in message:
                response = {
                    "errors": ["Requires msgType specified"],
                    "msgType": "Errors"
                }
                logging.info(response)
                await ws.send_message(json.dumps(response))
                continue
            if json.loads(message)['msgType'] == 'newBounds' and 'data' in message:
                new_bounds = json.loads(message)['data']
                bounds.update(new_bounds)
                await ws.send_message('OK')
            else:
                response = {
                    "errors": ["Requires valid JSON"],
                    "msgType": "Errors"
                }
                await ws.send_message(json.dumps(response))
            await trio.sleep(1)
        except ConnectionClosed:
            break
        except json.JSONDecodeError:
            response = {
                "errors": ["Requires valid JSON"],
                "msgType": "Errors"
            }
            logging.info(response)
            await ws.send_message(json.dumps(response))
            continue
        except TypeError:
            response = {
                "errors": ["Requires valid JSON"],
                "msgType": "Errors"
            }
            logging.info(response)
            await ws.send_message(json.dumps(response))
            continue


async def sent_to_browser(ws, buses_on_map, bounds):
    while True:
        try:
            buses_in_bounds = []
            for bus in buses_on_map:
                if WindowBounds.is_inside(bounds, bus.lat, bus.lng):
                    buses_in_bounds.append(asdict(bus))
                    logging.info(f'{len(buses_in_bounds)} buses inside bounds')
            response = {
                "msgType": "Buses",
                "buses": buses_in_bounds
            }
            if buses_in_bounds:
                await ws.send_message(json.dumps(response))
            await trio.sleep(0.1)
            logging.debug(response)
        except ConnectionClosed:
            break


async def talk_to_browser(request, buses_on_map):
    ws = await request.accept()
    bounds = WindowBounds()
    async with trio.open_nursery() as nursery:
        nursery.start_soon(sent_to_browser, ws, buses_on_map, bounds)
        nursery.start_soon(listen_browser, ws ,bounds)


async def start_server(bus_port, server_port):
    buses = []
    get_buses_coordinates = partial(get_coordinates, buses_on_map=buses)
    send_buses_coordinates_to_browser = partial(talk_to_browser, buses_on_map=buses)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, get_buses_coordinates, '127.0.0.1', bus_port, None)
        nursery.start_soon(serve_websocket, send_buses_coordinates_to_browser, '127.0.0.1', server_port, None)

@click.command()
@click.option('--bus_port', default=8080, help='Server address')
@click.option('--server_port', default=8000, help='Browser port')
@click.option('--v', default=False, help='Logging setup')
def main(bus_port, server_port, v):
    setup_logging(v)
    with contextlib.suppress(KeyboardInterrupt):
        trio.run(start_server, bus_port, server_port)

if __name__ == "__main__":
    main()
