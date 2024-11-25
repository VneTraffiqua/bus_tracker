import trio
from trio_websocket import serve_websocket, ConnectionClosed
import json
import aiofiles
import itertools


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


async def send_message(request):
    ws = await request.accept()

    while True:
        try:
            message = await ws.get_message()
            # message = json.dumps({
            #     "msgType": "Buses",
            #     "buses": [
            #         {"busId": "в420ор", "lat": item[0], "lng": item[1], "route": bus_data['name']},
            #         {"busId": "c790сс", "lat": 55.7500, "lng": 37.600, "route": "120"},
            #         {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"},
            #     ]
            # })
            # await ws.send_message(message)
            print(message)
            await trio.sleep(1)
        except ConnectionClosed:
            break


async def main():
    await serve_websocket(send_message, '127.0.0.1', 8080, ssl_context=None)


if __name__ == "__main__":
    trio.run(main)
