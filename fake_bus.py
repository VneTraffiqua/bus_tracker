import trio
import json
from trio_websocket import open_websocket_url, ConnectionClosed
import os


SLEEP_SEC=2


def load_routes(directory_path):
    for filename in os.listdir(directory_path):
        if filename.endswith(".json"):
            filepath = os.path.join(directory_path, filename)
            with open(filepath, 'r', encoding='utf8') as file:
                yield json.load(file)

async def broadcast_bus_route(route):
    while True:
        try:
            async with open_websocket_url('ws://127.0.0.1:8080') as ws:
                for item in route['coordinates']:
                    message = json.dumps(
                        {"busId": route['name'], "lat": item[0], "lng": item[1], "route": route['name']},
                        ensure_ascii=False
                    )
                    await ws.send_message(message)
                    await trio.sleep(SLEEP_SEC)
                    print(message)
        except ConnectionClosed:
            break

async def main():
    async with trio.open_nursery() as nursery:
        for route in load_routes('routes-1'):
            nursery.start_soon(broadcast_bus_route, route)


if __name__ == '__main__':
    trio.run(main)
