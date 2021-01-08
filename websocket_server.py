from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory, \
    listenWS
from twisted.internet import reactor
from autobahn.websocket.types import ConnectionDeny

from threading import Thread
import time

import random 
import txaio
txaio.use_twisted()

class BaseService:

    """
    Simple base for our services.
    """

    def __init__(self, proto):
        self.proto = proto

    def onOpen(self):
        pass
    def onClose(self, wasClean, code, reason):
        pass
    def onMessage(self, payload, isBinary):
        pass

class BroadcastInfoService(BaseService):  
    def onMessage(self, payload, isBinary):
        if "subscribe" in str(payload):
            self.proto.factory.sub_clients.append(self)
        elif "unsubscribe" in str(payload):
            self.proto.factory.sub_clients.remove(self)
        else:
            self.proto.sendMessage("Not valid action.".encode('utf8'))

    def onClose(self, wasClean, code, reason):
        print("Connection closed: {}".format(reason))

    def connectionLost(self, reason):
        print("Socket lost connection")
        WebSocketServerProtocol.connectionLost(self, reason)
        self.factory.unregister(self)

class HubServerProtocol(WebSocketServerProtocol):
    SERVICEMAP = {
        '/info': BroadcastInfoService
    }

    def __init__(self):
        WebSocketServerProtocol.__init__(self)
        self.service = None

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))
        if request.path in self.SERVICEMAP:
            self.service = self.SERVICEMAP[request.path](self)
            self.factory.register(self)
        else:
            err = "No service under %s" % request.path
            self.sendMessage("Not valid service.")    
        
    def onOpen(self):
        if self.service:    
            print("WebSocket connection open.")
            self.service.onOpen()      

    def onMessage(self, payload, isBinary):
        if self.service:
            print("Text message received: {0}".format(payload.decode('utf8')))
            self.service.onMessage(payload, isBinary)     
        
    def onClose(self, wasClean, code, reason):
        if self.service:
            print("Closing socket")
            self.factory.unregister(self)
            self.service.onClose(wasClean, code, reason)


class HubServerFactory(WebSocketServerFactory):
    def __init__(self, url, debug=False, debugCodePaths=False):
        WebSocketServerFactory.__init__(self, url)
        self.clients = []

        self.sub_clients = []
        info_thread = Thread(target = self.broadcast_info, daemon=True)
        info_thread.start()
        

    def register(self, client):
        if client not in self.clients:
            print("Registering client {}".format(client.peer))
            self.clients.append(client)

    def unregister(self, client):
        if client in self.clients:
            print("Unregistering client {}".format(client.peer))
            self.clients.remove(client)

    def subscribe(self, client):
        if client not in self.sub_clients:
            self.sub_clients.append(client)

    def unsubscribe(self, client):
        if client in self.sub_clients:
            self.sub_clients.remove(client)

    def broadcast_info(self):
        msg = [{"ticker":"NCTY","event":"SHORT","quant":50,"cost":3.57},
        {"ticker":"AAPL","event":"BUY","quant":100,"cost":356.20},
        {"ticker":"MSFT","event":"SHORT","quant":50,"cost":157.32},
        {"ticker":"NCTY","event":"LONG","quant":10,"cost":167.23}]
        
        while (True):
            if self.sub_clients:
                curr = str(msg[random.randint(0,3)]).encode("utf8")
                for client in self.sub_clients:
                    try:
                        client.proto.sendMessage(curr)
                    except Exception as e:
                        self.unsubscribe(client)
                        self.unregister(client)
                time.sleep(2)

    def broadcast(self, message):
        for client in self.clients:
            client.sendMessage(message)

if __name__ == '__main__':

    ServerFactory = HubServerFactory
    factory = ServerFactory("ws://127.0.0.1:9000")
    factory.protocol = HubServerProtocol
    listenWS(factory)

    reactor.run()