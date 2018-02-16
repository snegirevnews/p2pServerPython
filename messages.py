import json
import cryptotools

nonce = lambda: cryptotools.generate_nodeid()

class InvalidSignatureError(Exception):
    pass

class InvalidNonceError(Exception):
    pass

def make_envelope(msgtype, msg, nodeid): #использую
    msg['nodeid'] = nodeid
    msg['nonce'] =  nonce()
    envelope = {'data': msg,
                'msgtype': msgtype}
    return json.dumps(envelope) # еще раз сериализуем

def envelope_decorator(nodeid, func):
    msgtype = func.__name__.split("_")[0]
    def inner(*args, **kwargs):
        return make_envelope(msgtype, func(*args, **kwargs), nodeid)
    return inner

# ------

def create_hello(nodeid, version): #использую
    msg = {'version': version}
    return make_envelope("hello", msg, nodeid) #msgtype= hello

def create_addr(nodeid, nodes): #использую
    msg = {'nodes': nodes}
    return make_envelope("addr", msg, nodeid)

def create_ping(nodeid):
    msg = {}
    return make_envelope("ping", msg, nodeid)

def create_pong(nodeid):
    msg = {}
    return make_envelope("pong", msg, nodeid)

def create_block(nodeid): #использую
    msg = {'block': "OK"}
    return make_envelope("block", msg, nodeid)

# -------

def read_envelope(message): # возвращаю в формат json
    message = message.decode('utf8')
    return json.loads(message)

def read_message(message): # разбираю пришедшее сообщение
    message = message.decode('utf8')
    envelope = json.loads(message)
    return envelope['data']
