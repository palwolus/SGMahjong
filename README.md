#  Singapore Mahjong

A simple Singapore Mahjong game built using Python. Main libraries used is Pygame and SocketIO.

Game make use of Websocket to communicate with one another.

Requires 1 Mahjong Server to be running and 4 Mahjong Client to be connected to the Server (all done via websocket)

This was done during the circuit breaker period for fun with friends.

### How To Run

Before running the Server/Client, make sure to install Python and virtualenv. Followed by running the requirements.txt file.

#### Before Running Anything

You will need to download Mahjong Tiles images and drop it inside the `client/tile_pack/` folder.
The images have to be `png` file and named properly. (refer to README.txt in the folder for how to name the images)

#### Server

1) In the server folder, run `python3 app.py -port 5000` 
If `-port` is not specified, default to 5000

2) Do port forwarding for the port number that you specified or default port number

#### Client

1) In the client folder, run `python3 client.py`, followed by a few arguments

- `-name <your name>` 
- `-key <a secret key>` Must be >10 characters
- `-address <address>` The server address, e.g. `http://server.com:5000`
- So it should look like this: 
  - `python3 client.py -name Test -key 1234567890 -address https://localhost:5000/`

2) Wait for all players to connect to run the client. (should be 4 clients connecting)

3) Any client click on the Ping button, followed by Start, will start the game.

4) Let the game begin



Once again, this game is built during the circuit breaker for fun.