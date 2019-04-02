#!/usr/bin/env python

from flask import Flask, jsonify, request, Response
import datetime
import functools
import logging
import os
import random
import signal
import time
import requests

__version__ = "1.3"
PORT = os.getenv("PORT", 5000)
HOSTNAME = os.getenv("HOSTNAME")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
REQUEST_LIMIT = os.getenv("REQUEST_LIMIT", 5)
CONSUL_IP = os.getenv("CONSUL_IP", "host.docker.internal")
POD_IP = os.getenv("POD_IP")

app = Flask(__name__)

request_timestamps = []

def register_consul():
    url = "http://%s:8500/v1/catalog/register" % CONSUL_IP
    svc = "%s-consul" % HOSTNAME
    payload = {"Datacenter": "dc1", "Node": "qotm","Address": str(POD_IP),"Service": {"Service": str(svc), "Address": str(POD_IP), "Port": 80}}

    logging.info(url)
    logging.info(payload)
    try:
        r = requests.put(url, json=payload)
        logging.info("Registered service: %s with IP: %s to Consul." % (svc, POD_IP))
        return
    except requests.ConnectionError:
        logging.info("No consul agent found. Skipping registration.")
        return

def get_rpm():
    now = datetime.datetime.utcnow()

    count = 0

    global request_timestamps
    for t in request_timestamps:
        delta = now - t
        if delta.seconds <= 60:
            count += 1
    return count

# Quote storage
#
# Obviously, this would more typically involve a persistent backing store. That's not
# really needed for a demo though.

quotes = [
    "Abstraction is ever present.",
    "A late night does not make any sense.",
    "A principal idea is omnipresent, much like candy.",
    "Nihilism gambles with lives, happiness, and even destiny itself!",
    "The light at the end of the tunnel is interdependent on the relatedness of motivation, subcultures, and management.",
    "Utter nonsense is a storyteller without equal.",
    "Non-locality is the driver of truth. By summoning, we vibrate.",
    "A small mercy is nothing at all?",
    "The last sentence you read is often sensible nonsense.",
    "668: The Neighbor of the Beast."
]

# Utilities


class RichStatus (object):
    def __init__(self, ok, **kwargs):
        self.ok = ok
        self.info = kwargs
        self.info['hostname'] = HOSTNAME
        self.info['time'] = datetime.datetime.now().isoformat()
        self.info['version'] = __version__

    # Remember that __getattr__ is called only as a last resort if the key
    # isn't a normal attr.
    def __getattr__(self, key):
        return self.info.get(key)

    def __bool__(self):
        return self.ok

    def __nonzero__(self):
        return bool(self)

    def __contains__(self, key):
        return key in self.info

    def __str__(self):
        attrs = ["%s=%s" % (key, self.info[key])
                 for key in sorted(self.info.keys())]
        astr = " ".join(attrs)

        if astr:
            astr = " " + astr

        return "<RichStatus %s%s>" % ("OK" if self else "BAD", astr)

    def toDict(self):
        d = {'ok': self.ok}

        for key in self.info.keys():
            d[key] = self.info[key]

        return d

    @classmethod
    def fromError(self, error, **kwargs):
        kwargs['error'] = error
        return RichStatus(False, **kwargs)

    @classmethod
    def OK(self, **kwargs):
        return RichStatus(True, **kwargs)


def standard_handler(f):
    func_name = getattr(f, '__name__', '<anonymous>')

    @functools.wraps(f)
    def wrapper(*args, **kwds):
        rc = RichStatus.fromError("impossible error")
        session = request.headers.get('x-qotm-session', None)
        username = request.headers.get('x-authenticated-as', None)

        logging.debug("%s %s: session %s, username %s, handler %s" %
                      (request.method, request.path, session, username, func_name))

        headers_string = ', '.join("{!s}={!r}".format(key, val)
                                   for (key, val) in request.headers.items())
        logging.debug("headers: %s" % (headers_string))

        try:
            rc = f(*args, **kwds)
        except Exception as e:
            logging.exception(e)
            rc = RichStatus.fromError("%s: %s %s failed: %s" % (
                func_name, request.method, request.path, e))

        code = 200

        # This, candidly, is a bit of a hack.

        if session:
            rc.info['session'] = session

        if username:
            rc.info['username'] = username

        if not rc:
            if 'status_code' in rc:
                code = rc.status_code
            else:
                code = 500

        resp = jsonify(rc.toDict())
        resp.status_code = code

        if session:
            resp.headers['x-qotm-session'] = session

        return resp

    return wrapper

# REST endpoints

####
# GET /health does a basic health check. It always returns a status of 200
# with an empty body.


@app.route("/health", methods=["GET", "HEAD"])
@standard_handler
def health():
    return RichStatus.OK(msg="QotM health check OK")

####
# GET / returns a random quote as the 'quote' element of a JSON dictionary. It
# always returns a status of 200.


@app.route("/", methods=["GET"])
@standard_handler
def statement():
    # return RichStatus.OK(quote="Telepresence rocks!")
    return RichStatus.OK(quote=random.choice(quotes))

####
# GET /limited/ calls get_rpm to get the requests per minute to the endpoint.
# If less than REQUEST_LIMIT, it returns a random quote same as the method 
# above. If greater, it returns a 500 to simulate an overloaded server.
#
# GET /limited/clear clears the global array that stores timestamps used to
# check if a request is over the limit.


@app.route("/limited/", methods=["GET"])
@standard_handler
def request_limited():

    global request_timestamps
    request_timestamps.append(datetime.datetime.utcnow())

    if get_rpm() > int(REQUEST_LIMIT):
        return "App Overloaded", 500
    
    return RichStatus.OK(quote=random.choice(quotes))

@app.route("/limited/clear", methods=["GET"])
@standard_handler
def clear_timestamps():

    global request_timestamps
    request_timestamps = []

    return RichStatus.OK()



####
# GET /quote/quoteid returns a specific quote. 'quoteid' is the integer index
# of the quote in our array above.
#
# - If all goes well, it returns a JSON dictionary with the requested quote as
#   the 'quote' element, with status 200.
# - If something goes wrong, it returns a JSON dictionary with an explanation
#   of what happened as the 'error' element, with status 400.
#
# PUT /quote/quotenum updates a specific quote. It requires a JSON dictionary
# as the PUT body, with the the new quote contained in the 'quote' dictionary
# element.
#
# - If all goes well, it returns the new quote as if you'd requested it using
#   the GET verb for this endpoint.
# - If something goes wrong, it returns a JSON dictionary with an explanation
#   of what happened as the 'error' element, with status 400.

@app.route("/quote/<idx>", methods=["GET", "PUT"])
@standard_handler
def specific_quote(idx):
    try:
        idx = int(idx)
    except ValueError:
        return RichStatus.fromError("quote IDs must be numbers", status_code=400)

    if (idx < 0) or (idx >= len(quotes)):
        return RichStatus.fromError("no quote ID %d" % idx, status_code=400)

    if request.method == "PUT":
        j = request.json

        if (not j) or ('quote' not in j):
            return RichStatus.fromError("must supply 'quote' via JSON dictionary", status_code=400)

        quotes[idx] = j['quote']

    return RichStatus.OK(quote=quotes[idx])

####
# POST /quote adds a new quote to our list. It requires a JSON dictionary
# as the POST body, with the the new quote contained in the 'quote' dictionary
# element.
#
# - If all goes well, it returns a JSON dictionary with the new quote's ID as
#   'quoteid', and the new quote as 'quote', with a status of 200.
# - If something goes wrong, it returns a JSON dictionary with an explanation
#   of what happened as the 'error' element, with status 400.


@app.route("/quote", methods=["POST"])
@standard_handler
def new_quote():
    j = request.json

    if (not j) or ('quote' not in j):
        return RichStatus.fromError("must supply 'quote' via JSON dictionary", status_code=400)

    quotes.append(j['quote'])

    idx = len(quotes) - 1

    return RichStatus.OK(quote=quotes[idx], quoteid=idx)


@app.route("/crash", methods=["GET"])
@standard_handler
def crash():
    logging.warning("dying in 1 seconds")
    time.sleep(1)
    os.kill(os.getpid(), signal.SIGTERM)
    time.sleep(1)
    os.kill(os.getpid(), signal.SIGKILL)

# Mainline


def main():
    register_consul()
    app.run(debug=False, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    logging.basicConfig(
        # filename=logPath,
        level=LOG_LEVEL,  # if appDebug else logging.INFO,
        format="%%(asctime)s QotM %s %%(levelname)s: %%(message)s" % __version__,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logging.info("initializing on %s:%d" % (HOSTNAME, PORT))
    main()
