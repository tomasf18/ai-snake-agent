import asyncio
import datetime
import getpass
import json
import os
import time
import websockets # type: ignore
from utils.snake import Snake
from utils.SnakeDomain import SnakeDomain

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        # extract the map info, first JSON received when joining the game
        map_info = json.loads(await websocket.recv())

        snake: Snake = Snake()
        domain: SnakeDomain = SnakeDomain(map = map_info)
        await domain.startupMap()

        while True:
            try:
                data = json.loads(await websocket.recv())  # receive game update, this must be called timely or your game will get out of sync with the server

                ts = datetime.datetime.fromisoformat(data["ts"]).timestamp()
                if (datetime.datetime.now().timestamp() - ts) > domain.time_per_frame:
                    # print("Received a message that is too old")
                    domain.multi_objectives.clear_goals()
                    domain.plan = []
                    continue
                

                
                snake.update(data)
            

                key = domain.get_next_move(snake=snake)
                
                await websocket.send(
                    json.dumps({"cmd": "key", "key": key})
                )  # send the key command to the server
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return
            
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"EXCEPTION... superfoods eaten = {domain.superfood_eaten}, food eaten = {domain.food_eaten}")


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))