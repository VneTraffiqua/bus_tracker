import trio
from sys import stderr
import json
from trio_websocket import open_websocket_url, ConnectionClosed
import itertools


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

async def main():
    bus_data = read_json_file('./156.json')
    for item in itertools.cycle(bus_data['coordinates']):
        try:
            async with open_websocket_url('ws://127.0.0.1:8080') as ws:
                message = json.dumps(
                        {"busId": "в420ор", "lat": item[0], "lng": item[1], "route": bus_data['name']},
                )
                await ws.send_message(message)
                await trio.sleep(2)
                print(message)
        except ConnectionClosed:
            break

trio.run(main)