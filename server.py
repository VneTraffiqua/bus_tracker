import trio
from trio_websocket import serve_websocket, ConnectionClosed
from functools import partial
import json
import logging


logging.basicConfig(
        format=u'%(filename)s[LINE:%(lineno)d]# %(levelname)-4s [%(asctime)s]  %(message)s',
        level=logging.INFO,
        filename='server_logger.log'
    )

def is_inside(bounds, lat, lng):
    return bounds['south_lat'] <= lat <= bounds['north_lat'] and bounds['west_lng'] <= lng <= bounds['east_lng']


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
    ws = await request.accept()
    message = await ws.get_message()
    message = json.loads(message)
    buses = []
    for key, value in buses_on_map.items():
        if is_inside(message['data'],value['lat'], value['lng']):
            buses.append(value)
            logging.info(message)
            logging.info(f'{len(buses)} buses inside bounds')
    response = {
        "msgType": "Buses",
        "buses": buses
    }
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
