from simple_websocket_server import WebSocket, WebSocketServer
from uuid import UUID, uuid4
import json
import time

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

class Stroke:
    def __init__(self, color: str, points: list[list[int, int]], lineSize: int, isMarker: bool):
        self.color: str = color
        self.points: list[list[int, int]] = points
        self.lineSize: int = lineSize
        self.isMarker: bool = isMarker
        self.createdTime = time.time() # for deleting if we feel like it
        
        self.verifyAndCorrectData() # make sure everything is good
    
    def toJson(self) -> dict:
        return {
            "color": self.color,
            "points": self.points,
            "lineSize": self.lineSize,
            "isMarker": self.isMarker,
        }
    
    def verifyAndCorrectData(self) -> None:
        # fix points
        for i in range(0, len(self.points)):
            p = self.points[i]
            if p[0] < 0: self.points[i][0] = 0
            if p[0] > CANVAS_WIDTH: self.points[i][0] = CANVAS_WIDTH
            
            if p[1] < 0: self.points[i][0] = 0
            if p[1] > CANVAS_HEIGHT: self.points[i][0] = CANVAS_HEIGHT
        
        if self.lineSize <= 0: self.lineSize = 1
        if self.lineSize > 16: self.lineSize = 16

def jsonToStroke(json: dict) -> Stroke:
    if len(json["points"]) == 0: return None
    if "color" not in json: return None
    if "points" not in json: return None
    if "lineSize" not in json: return None
    if "isMarker" not in json: return None
    
    s = Stroke( json["color"], json["points"], json["lineSize"], json["isMarker"] )
    return s

class Client:
    def __init__(self, socket):
        self.socket = socket
        self.uuid: UUID = uuid4()
        self.strokes: list[Stroke] = []
    
    def getSocket(self): return self.socket
    def getUUID(self) -> UUID: return self.uuid
    def getStrokes(self) -> list[Stroke]: return self.strokes
    def setStrokes(self, strokes: list[Stroke]) -> None: self.strokes = strokes

clients: list[Client] = []

def getClientIndex(uuid: UUID) -> int:
    for i in range(0, len(clients)):
        if clients[i].getUUID() == uuid: return i
    return -1

def getClient(uuid: UUID) -> Client:
    return clients[ getClientIndex(uuid) ]


class GameServerWebsocket(WebSocket):
    def connected(self):
        c = Client(self)
        clients.append(c)
        
        self.uuid = c.getUUID()
        uuidPacket = {
            "purpose": "SetUUID",
            "uuid": str(self.uuid)
        }
        self.send_message(json.dumps(uuidPacket))
        
        # Send all other clients' strokes
        for otherClient in clients:
            if otherClient.getUUID() == self.uuid: continue
            packet = self.makeStrokesPacket(otherClient.getUUID())
            self.send_message(packet)
        
        print(f"{self.address} connected!")
    
    def sendAllOtherClients(self, message: str):
        index = getClientIndex(self.uuid)
        for i in range(0, len(clients)):
            if i == index: continue
            clients[i].getSocket().send_message(message)
    
    def makeStrokesPacket(self, uuid) -> str:
        strokes = []
        for s in getClient(uuid).getStrokes(): strokes.append( s.toJson() )
        
        packetData = {
            "purpose": "UserStrokes",
            "uuid": str(uuid),
            "strokes": strokes,
        }
        return json.dumps(packetData)
    
    def handle(self):
        try: data = json.loads(self.data)
        except: raise Exception(f"Data received is not JSON! Received:\n\"\"\"\n{self.data}\n\"\"\"")
        
        packetPurpose = data["purpose"]
        if packetPurpose == "SendMyStrokes":
            strokes: list[Stroke] = []
            rawStrokes = data["strokes"]
            for raw in rawStrokes:
                s: Stroke = jsonToStroke(raw)
                if s == None: continue
                strokes.append(s)
            
            i = getClientIndex(self.uuid)
            clients[i].setStrokes(strokes)
            
            self.sendAllOtherClients(self.makeStrokesPacket(self.uuid))
    
    def handle_close(self):
        print(f"{self.address} disconnected!")
        
        clients[getClientIndex(self.uuid)].setStrokes([])
        self.sendAllOtherClients(self.makeStrokesPacket(self.uuid))
        clients.pop(getClientIndex(self.uuid))
        

server = WebSocketServer("0.0.0.0", 8080, GameServerWebsocket)

print("Server running!")
server.serve_forever()