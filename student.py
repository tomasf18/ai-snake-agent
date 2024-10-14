import asyncio
import getpass
import json
import os
import websockets

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        # extract the map info, first JSON received when joining the game
        map_info = json.loads(await websocket.recv())
        print(map_info)

        while True:
            try:
                state = json.loads(await websocket.recv())  # receive game update, this must be called timely or your game will get out of sync with the server
                print(state)
                
                # extract information from the state
                level = state["level"]  # get the level (provavelmente não é necessário -----------)
                step = state["step"]  # get the step (provavelmente não é necessário -----------)
                timeout = state["timeout"]  # get the timeout (provavelmente não é necessário -----------)
                
                food_position = state["food"][0][0:2]  # get the food position
                food_type = state["food"][0][2]  # get the food type
                
                timestamp = state["ts"]  # get the timestamp (provavelmente não é necessário -----------)
                name = state["name"]  # get the snake name (provavelmente não é necessário -----------)
                
                snake_body = state["body"]  # get the snake body positions
                snake_head = snake_body[0]  # get the snake head position
                snake_tail = snake_body[-1]  # get the snake tail position
                snake_sight = state["sight"]  # get the snake sight
                score = state["score"]  # get the score
                snake_range = state["range"]  # get the snake range
                snake_traverse = state["traverse"]  # get the snake traverse
                
                key = ""
                
                # simple logic to move the snake to the food
                if snake_head[0] < food_position[0]:
                    key = "d" # move right
                elif snake_head[0] > food_position[0]:
                    key = "a" # move left
                elif snake_head[1] < food_position[1]:
                    key = "s" # move down
                elif snake_head[1] > food_position[1]:
                    key = "w" # move up

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
