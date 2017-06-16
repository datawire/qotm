#!/usr/bin/env python

import os
import datetime
import random

from flask import Flask, jsonify
app = Flask(__name__)

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

@app.route("/", methods=["GET"])
def statement():
    return jsonify(quote=random.choice(quotes),
                   hostname=os.getenv("HOSTNAME"),
                   time=datetime.datetime.now().isoformat()),


@app.route("/health", methods=["GET", "HEAD"])
def health():
    return "", 200


def main():
    app.run(debug=False, host="0.0.0.0")


if __name__ == "__main__":
    main()
