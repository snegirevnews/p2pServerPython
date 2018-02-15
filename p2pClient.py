from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
from twisted.internet.task import LoopingCall
from functools import partial

import cryptotools
import messages
from time import time

PING_INTERVAL = 1200.0 #каждые 20 минут я проверяю на активность

class MyProtocol(Protocol):
    def __init__(self, factory, state="GETHELLO", kind="LISTENER"):
        self.factory = factory
        self.state = state
        self.VERSION = 0
        self.remote_nodeid = None
        self.kind = kind
        self.nodeid = self.factory.nodeid
        self.lc_ping = LoopingCall(self.send_PING)
        self.message = partial(messages.envelope_decorator, self.nodeid)

    def connectionMade(self):
        remote_ip = self.transport.getPeer()
        host_ip = self.transport.getHost()
        self.remote_ip = remote_ip.host + ":" + str(remote_ip.port)
        self.host_ip = host_ip.host + ":" + str(host_ip.port)
        print ("Connection from", self.transport.getPeer())

    def connectionLost(self, reason):
        try:
            self.lc_ping.stop()
        except AssertionError:
            pass

        try:
            self.factory.peers.pop(self.remote_nodeid)
        except KeyError:
            if self.nodeid != self.remote_nodeid:
                print(" [ ] GHOST LEAVES: from", self.remote_nodeid, self.remote_ip)

    def dataReceived(self, data):
        for line in data.splitlines():
            line = line.strip()
            envelope = messages.read_envelope(line)
            print(self.state)
            if self.state in ["GETHELLO", "SENTHELLO"]:
                if envelope['msgtype'] == 'hello':
                    self.handle_HELLO(line)
                else:
                    print(" [!] Ignoring", envelope['msgtype'], "in", self.state)
            else:
                if envelope['msgtype'] == 'ping':
                    self.handle_PING(line)
                elif envelope['msgtype'] == 'pong':
                    self.handle_PONG(line)
                elif envelope['msgtype'] == 'addr':
                    self.handle_ADDR(line)

    def send_HELLO(self):
        hello = messages.create_hello(self.nodeid, self.VERSION)
        print("SEND_HELLO:", self.nodeid, "to", self.remote_ip)
        self.transport.write(hello + "\n")
        self.state = "SENTHELLO" #состояние SENTHELLO

    def handle_HELLO(self, hello):
        try:
            print("Получил HELLO")
            hello = messages.read_message(hello)
            self.remote_nodeid = hello['nodeid'] #nodeid того,кто прислал письмо
            if self.remote_nodeid == self.nodeid: #если я  сам себе прислал
                print(" [!] Found myself at", self.host_ip)
                self.transport.loseConnection()
            else: #если я не сам себе прислал
                if self.state == "GETHELLO": #если я в состоянии GETHELLO
                    my_hello = messages.create_hello(self.nodeid, self.VERSION) #собираю свое Hello- сообщение
                    self.transport.write(my_hello + "\n") #отправляю
                self.add_peer() # добавить данный пир в List
                self.state = "READY" #ставлю себе состояние READY
                # self.print_peers()
                # self.write(messages.create_ping(self.nodeid))
                if self.kind == "LISTENER": #если я СЛУШАЮ, то начинаю пинговать Пира
                    print(" [ ] Starting pinger to " + self.remote_nodeid)
                    self.lc_ping.start(PING_INTERVAL, now=False)
                    # Tell new audience about my peers
                    self.send_ADDR()
        except messages.InvalidSignatureError: #если в ходе передачи были искажены данные
            print(" [!] ERROR: Invalid hello sign ", self.remoteip)
            self.transport.loseConnection()

    def add_peer(self): #добавление Пира в Лист
        entry = (self.remote_ip, self.kind, time())
        self.factory.peers[self.remote_nodeid] = entry

    def send_ADDR(self): #Рассказываю данному ноду о моих пирах.
        print("Telling " + self.remote_nodeid + " about my peers")
        peers = self.factory.peers
        listeners = [(n, peers[n][0], peers[n][1], peers[n][2])
                     for n in peers]
        addr = messages.create_addr(self.nodeid, listeners)
        self.write(addr)

    def handle_ADDR(self, addr):
        try:
            nodes = messages.read_message(addr)['nodes']
            print("Recieved addr list from peer " + self.remote_nodeid)
            for node in nodes:
                print(" " + node[0] + " " + node[1])
                if node[0] == self.nodeid:
                    print(" [!] Not connecting to " + node[0] + ": thats me!")
                    return
                if node[1] != "SPEAKER":
                    print(" [ ] Not connecting to " + node[0] + ": is " + node[1])
                    return
                if node[0] in self.factory.peers:
                    print(" [ ] Not connecting to " + node[0] + ": already connected")
                    return
                print(" [ ] Trying to connect to peer " + node[0] + " " + node[1])
                host, port = node[0].split(":")
                point = TCP4ClientEndpoint(reactor, host, int(port))
                d = connectProtocol(point, MyProtocol(self.factory, "SENDHELLO", "SPEAKER"))
                d.addCallback(gotProtocol)
        except messages.InvalidSignatureError:
            print (addr)
            print("ERROR: Invalid addr sign ", self.remote_ip)
            self.transport.loseConnection()

    def send_PING(self):
        print("PING   to", self.remote_nodeid, "at", self.remote_ip)
        ping = messages.create_ping(self.nodeid)
        self.write(ping)

    def handle_PING(self, ping):
        if messages.read_message(ping):
            pong = messages.create_pong(self.nodeid)
            self.write(pong)

    def handle_PONG(self, pong):
        pong = messages.read_message(pong)
        print("PONG from", self.remote_nodeid, "at", self.remote_ip)
        addr, kind = self.factory.peers[self.remote_nodeid][:2]
        self.factory.peers[self.remote_nodeid] = (addr, kind, time())

class MyFactory(Factory):
    def __init__(self):
        pass

    def startFactory(self):
        self.peers = {}
        self.numProtocols = 0
        self.nodeid = cryptotools.generate_nodeid()[:10]
        print(" [ ] NODEID:", self.nodeid)

    def stopFactory(self):
        pass

    def buildProtocol(self, addr):
        return MyProtocol(self, "GETHELLO", "LISTENER")

def gotProtocol(p):
    p.send_HELLO()
