from flask import g
import sqlite3
from os import environ, path
from flask import Flask, request, jsonify
import requests

BOT_TOKEN = environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = environ.get('TELEGRAM_WEBHOOK_URL')


def set_webhook():
    set_webhook_url = f'https://api.telegram.org/bot{BOT_TOKEN}/setWebHook?url={WEBHOOK_URL}'
    webhook_response = requests.get(set_webhook_url)
    return webhook_response


set_webhook_response = set_webhook()
print(set_webhook_response.text)


DATABASE = 'database.db'

app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db():
    cur = get_db().execute('SELECT status FROM led')
    res = cur.fetchone()
    cur.close()
    return res[0]


def update_db(status_text):
    db = get_db()
    cur = db.execute('UPDATE led SET status = ?', (status_text,))
    db.commit()
    cur.close()


@app.route('/', methods=['POST', 'GET'])
def telegram():
    led_status = '...'
    if request.method == 'POST':
        data_body = request.get_json()
        message = data_body.get('message')
        username = message.get('from').get('username')
        chat_id = message.get('chat').get('id')
        answer = f"{username}: LED is now {message.get('text')}"
        update_db(message.get('text'))
        resp = requests.post(f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?POST',
                             json={'chat_id': chat_id, 'text': answer})
        return jsonify(resp.json()), resp.status_code
    if request.method == 'GET':
        led_status = query_db()
        print(led_status)
        return jsonify({'led_status': led_status}), 200
