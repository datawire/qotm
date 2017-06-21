#!/usr/bin/env python

import os
import datetime
import random

from flask import Flask, jsonify, request
app = Flask(__name__)

######## Quote storage
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

######## Utilities

def result(**kwargs):
    """
    Pack up a bunch of keyword args into a JSONified dictionary, and make sure
    that the hostname and time are included.
    """

    d = dict(kwargs)
    d['hostname'] = os.getenv("HOSTNAME")
    d['time'] = datetime.datetime.now().isoformat()

    return jsonify(**d)

######## REST endpoints

####
# GET /health does a basic health check. It always returns a status of 200
# with an empty body.

@app.route("/health", methods=["GET", "HEAD"])
def health():
    return "", 200

####
# GET / returns a random quote as the 'quote' element of a JSON dictionary. It 
# always returns a status of 200.

@app.route("/", methods=["GET"])
def statement():
    return result(quote=random.choice(quotes)), 200

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
def specific_quote(idx):
    try:
        idx = int(idx)
    except ValueError:
        return result(error="quote IDs must be numbers"), 400

    if (idx < 0) or (idx >= len(quotes)):
        return result(error="no quote ID %d" % idx), 400

    if request.method == "PUT":
        j = request.json

        if (not j) or ('quote' not in j):
            return result(error="must supply 'quote' via JSON dictionary"), 400

        quotes[idx] = j['quote']

    return result(quote=quotes[idx]), 200

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
def new_quote():
    j = request.json

    if (not j) or ('quote' not in j):
        return result(error="must supply 'quote' via JSON dictionary"), 400

    quotes.append(j['quote'])

    idx = len(quotes) - 1

    return result(quoteid=idx, quote=quotes[idx]), 200

######## Mainline

def main():
    app.run(debug=True, host="0.0.0.0")

if __name__ == "__main__":
    main()
