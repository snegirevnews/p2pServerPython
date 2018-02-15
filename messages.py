import hmac
import json
import cryptotools

nonce = lambda: cryptotools.generate_nodeid()
incr_nonce = lambda env: format(int(env["nonce"], 16) + 1, 'x')

class InvalidSignatureError(Exception):
    pass

class InvalidNonceError(Exception):
    pass

def make_envelope(msgtype, msg, nodeid): #использую
    msg['nodeid'] = nodeid
    msg['nonce'] =  nonce()
    data = json.dumps(msg) #сериализуем
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

# -------

def read_envelope(message): # возвращаю в формат json
    return json.loads(message)

def read_message(message): # разбираю пришедшее сообщение
    envelope = json.loads(message)
    # nodeid = str(envelope['data']['nodeid'])
    # signature = str(envelope['sign'])
    # msg = json.dumps(envelope['data'])
    # verify_sign = hmac.new(nodeid, msg)
    return envelope['data']
    # if hmac.compare_digest(verify_sign.hexdigest(), signature):
    #
    # else:
    #     raise InvalidSignatureError
