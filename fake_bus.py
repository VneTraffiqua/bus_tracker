import trio
import json
from trio_websocket import open_websocket_url, ConnectionClosed
import os
import itertools
from random import randint

SLEEP_SEC=0


def generate_bus_id(route_id, bus_index):
    return f"{route_id}-{bus_index}"

def load_routes(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)

async def broadcast_bus_route(reader):
    async with open_websocket_url('ws://127.0.0.1:8080') as ws:
        async for message in reader:
            await ws.send_message(message)
            await trio.sleep(SLEEP_SEC)


async def run_bus(route, writer):
    while True:
        try:
            random_start = randint(0, len(route['coordinates']))
            bus_route_with_random_start = itertools.cycle(
                itertools.islice(route['coordinates'], random_start, None)
            )
            bus_id = generate_bus_id(route['name'], randint(0, 1000))
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
        except ConnectionClosed:
            break

async def main():
    writer, reader = trio.open_memory_channel(10)
    async with trio.open_nursery() as nursery:
        for route in load_routes('routes'):
            for _ in range(40):
                nursery.start_soon(run_bus, route, writer)
        for _ in range(20):
            nursery.start_soon(broadcast_bus_route, reader)

if __name__ == '__main__':
    trio.run(main)
