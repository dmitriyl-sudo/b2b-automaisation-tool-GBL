# save as webhook.py
from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["POST"])
def webhook():
    print("Got webhook:", request.json)
    return "", 202

app.run(port=8002)
