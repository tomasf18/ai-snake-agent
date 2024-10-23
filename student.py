import asyncio
import getpass
import json
import os
import websockets
from snake import Snake
from SnakeDomain import SnakeDomain

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        # extract the map info, first JSON received when joining the game
        map_info = json.loads(await websocket.recv())
        print(map_info)
        
        snake: Snake = Snake()
        domain: SnakeDomain = SnakeDomain(map = map_info)
        await domain.startupMap()

        while True:
            try:
                data = json.loads(await websocket.recv())  # receive game update, this must be called timely or your game will get out of sync with the server
                print(data)
                snake.update(data)

                key = domain.get_next_move(snake=snake)
                
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send the key command to the server
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))