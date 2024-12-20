import trio
import json
from trio_websocket import open_websocket_url, ConnectionClosed, HandshakeError
import os
import itertools
from random import randint
import click
import contextlib
import logging


def setup_logging(debug):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-4s [%(asctime)s]  %(message)s',
        level=level,
        filename='fake_bus_logger.log'
    )


def generate_bus_id(route_id, bus_index):
    bus_id = f'{route_id}-{bus_index}'
    logging.debug(f'Generated bus ID: {bus_id}')
    return bus_id

def load_routes(directory_path, routes_number):
    routes_count = 0
    logging.info(f'Loading routes from directory: {directory_path}')
    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            filepath = os.path.join(directory_path, filename)
            logging.info(f'Loading bus route: {filename}')
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)
            routes_count +=1
            if routes_count >= routes_number:
                logging.info(f'Loaded {routes_count} routes, stopping')
                break

async def broadcast_bus_route(reader, server, refresh_timeout):
    logging.info(f'Starting websocket connection to {server}:8080')
    async with open_websocket_url(f'ws://{server}:8080') as ws:
        async for message in reader:
            await ws.send_message(message)
            logging.debug(f'Sent message to websocket: {message}')
            await trio.sleep(refresh_timeout)

async def run_bus(route, writer, emulator_id):
    while True:
        try:
            random_start = randint(0, len(route['coordinates']))
            bus_route_with_random_start = itertools.cycle(
                itertools.islice(route['coordinates'], random_start, None)
            )
            if emulator_id:
                bus_id = generate_bus_id(route['name'], randint(0, 1000))
            else:
                bus_id = route['name']
            for item in bus_route_with_random_start:
                message = json.dumps(
                    {
                        "busId": bus_id,
                        "lat": item[0],
                        "lng": item[1],
                        "route": route['name']
                    },
                    ensure_ascii=False
                )
                await writer.send(message)
                logging.debug(f'Generated bus position: {message}')
        except ConnectionClosed:
            logging.warning(f'Connection to websocket closed')
            break


async def generate_buses(buses_per_route, server, routes_number, websockets_number, emulator_id, refresh_timeout, v):
    writer, reader = trio.open_memory_channel(1)
    logging.info('Starting bus simulation...')
    while True:
        try:
            async with trio.open_nursery() as nursery:
                for route in load_routes('routes', routes_number):
                    for _ in range(buses_per_route):
                        nursery.start_soon(run_bus, route, writer, emulator_id)
                for _ in range(websockets_number):
                    nursery.start_soon(broadcast_bus_route, reader, server, refresh_timeout)
                logging.info(f'Started {buses_per_route * routes_number} buses on {websockets_number} websockets')
        except ExceptionGroup as eg:
            for exc in eg.exceptions:
                if isinstance(exc, (HandshakeError, ConnectionRefusedError)):
                    logging.info(f'HandshakeError. Connected to server {server} failed')
                    await trio.sleep(1)
                    continue

@click.command()
@click.option('--buses_per_route', default=1, help='Number of buses on each route')
@click.option('--server', default='127.0.0.1', help='Server address')
@click.option('--routes_number', default=200, help='Number of routes')
@click.option('--websockets_number', default=1, help='Number of open websockets')
@click.option('--emulator_id', default=True, help='Prefix to busId')
@click.option('--refresh_timeout', default=0, help='Delay in updating server coordinates')
@click.option('--v', default=False, help='Logging setup')
def main(buses_per_route, server, routes_number, websockets_number, emulator_id, refresh_timeout, v):
    setup_logging(v)
    with contextlib.suppress(KeyboardInterrupt):
        trio.run(
            generate_buses,
            buses_per_route, server, routes_number, websockets_number, emulator_id, refresh_timeout, v
        )

if __name__ == '__main__':
    main()
