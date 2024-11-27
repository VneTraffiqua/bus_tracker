import trio
from trio_websocket import serve_websocket, ConnectionClosed
from functools import partial
import json


async def get_coordinates(request, buses_on_map):
    ws = await request.accept()
    while True:
        try:
            message = await ws.get_message()
            message = json.loads(message)
            buses_on_map[message['busId']] = message
            # await trio.sleep(1)
        except ConnectionClosed:
            break


async def talk_to_browser(request, buses_on_map):
    response = {
        "msgType": "Buses",
        "buses": []
    }
    ws = await request.accept()
    for key, value in buses_on_map.items():
        response['buses'].append(value)
    print(response)
    await ws.send_message(json.dumps(response))


async def main():
    buses = {}
    get_buses_coordinates = partial(get_coordinates, buses_on_map=buses)
    send_buses_coordinates_to_browser = partial(talk_to_browser, buses_on_map=buses)
    async with trio.open_nursery() as nursery:
        nursery.start_soon(serve_websocket, get_buses_coordinates, '127.0.0.1', 8080, None)
        nursery.start_soon(serve_websocket, send_buses_coordinates_to_browser, '127.0.0.1', 8000, None)


if __name__ == "__main__":
    trio.run(main)
