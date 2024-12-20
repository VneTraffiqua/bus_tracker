import json
import pytest
from trio_websocket import open_websocket_url


TEST_MESSAGE_1 = '"dd"'
TEST_MESSAGE_2 = '{"msgType": "newBounds", "data": {"east_lng": 37.65563964843751, "north_lat": 55.77367652953477, "south_lat": 55.72628839374007, "west_lng": 37.54440307617188}}'
TEST_MESSAGE_3 = '{"msgType": "newBounds"}'
TEST_MESSAGE_4 = '{"msgType": "Buses", "buse": [{"busId": "c790сс", "lat": 55.75, "lng": 37.6, "route": "120"}, {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670к"}]}'
TEST_MESSAGE_5 = '{"msgType": "Buses", "buses": [{"busId": "c790\u0441\u0441", "lat": 155.75, "long": 37.6, "route": "120"}, {"busId": "a134aa", "lat": 55.7494, "lng": 37.621, "route": "670\u043a"}]}'

TEST_REPLY_1 = '{"errors": ["Requires msgType specified"], "msgType": "Errors"}'
TEST_REPLY_2 = 'OK'
TEST_REPLY_3 = '{"errors": ["Requires valid JSON"], "msgType": "Errors"}'
TEST_REPLY_4 = '{"errors": ["Requires valid JSON"], "msgType": "Errors"}'
TEST_REPLY_5 = '{"errors": ["Requires valid JSON"], "msgType": "Errors"}'

@pytest.fixture
async def server_client():
    async with open_websocket_url('ws://127.0.0.1:8000') as ws:
        yield ws

@pytest.fixture
async def fake_bus():
    async with open_websocket_url('ws://127.0.0.1:8080') as ws:
        yield ws

@pytest.mark.trio
async def test_browser_data(server_client):
    await server_client.send_message(TEST_MESSAGE_1)
    response_1 = await server_client.get_message()
    assert response_1 == TEST_REPLY_1

    await server_client.send_message(TEST_MESSAGE_2)
    response_2 = await server_client.get_message()
    assert response_2 == TEST_REPLY_2

    test_message2 = json.dumps(TEST_MESSAGE_3)
    await server_client.send_message(test_message2)
    response_3 = await server_client.get_message()
    print(response_3)
    assert response_3 == TEST_REPLY_3

@pytest.mark.trio
async def test_fake_bus(fake_bus):
    await fake_bus.send_message(TEST_MESSAGE_4)
    response_4 = await fake_bus.get_message()
    assert response_4 == TEST_REPLY_4

    await fake_bus.send_message(TEST_MESSAGE_5)
    response_5 = await fake_bus.get_message()
    assert response_5 == TEST_REPLY_5
