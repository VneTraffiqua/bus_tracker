import trio
from sys import stderr
import json
from trio_websocket import open_websocket_url, ConnectionClosed
import itertools
import os


def load_routes(directory_path='routes'):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


async def broadcast_bus_route(route):
    while True:
        try:
            async with open_websocket_url('ws://127.0.0.1:8080') as ws:
                    for item in route['coordinates']:
                        message = json.dumps(
                                {"busId": route['name'], "lat": item[0], "lng": item[1], "route": route['name']},
                        )
                        await ws.send_message(message)
                    await trio.sleep(1)
        except ConnectionClosed:
            break

async def main():
    # route = read_json_file('./156.json')
    # await broadcast_bus_route(route)
    async with trio.open_nursery() as nursery:
        for route in load_routes('./routes'):
            nursery.start_soon(broadcast_bus_route, route)


trio.run(main)
