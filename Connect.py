from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.internet.error import CannotListenError
from twisted.internet.endpoints import connectProtocol

import p2pClient
from p2pClient import MyFactory, MyProtocol


def connect():
    host = "" #адрес сервера
    port = 0 #порт сервера

    try:
        endpoint = TCP4ServerEndpoint(reactor, 5005)
        ncfactory = MyFactory()
        endpoint.listen(ncfactory)
        print("LISTEN")
    except CannotListenError:
        print("[!] Address in use")
        raise SystemExit

    point = TCP4ClientEndpoint(reactor, host, int(port))
    d = connectProtocol(point, MyProtocol(ncfactory, "SENDHELLO", "SPEAKER"))
    d.addCallback(p2pClient.gotProtocol)
    reactor.run()

if __name__ == "__main__":
    connect()
