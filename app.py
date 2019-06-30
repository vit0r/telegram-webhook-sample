from flask import g
import sqlite3
from os import environ, path
from flask import Flask, request, jsonify
import requests

BOT_TOKEN = environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = environ.get('TELEGRAM_WEBHOOK_URL')
SEND_MESSAGE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?POST'


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
    return res[0] if isinstance(res, tuple) else None


def update_db(status_text, user_id):
    db = get_db()
    cur = db.execute(
        'UPDATE led SET status = ? WHERE user_id = ?', (status_text, user_id))
    db.commit()
    cur.close()


def post_status(request_json):
    message = request_json.get('message')
    print(message)
    cmd = message.get('text').replace('/', '')
    if cmd not in ['on', 'off']:
        return jsonify({'ok': False}), 200
    username = message.get('from').get('username')
    chat_id = message.get('chat').get('id')
    answer = f"{username}: LED is now {cmd}"
    update_db(cmd, chat_id)
    post_json = {'chat_id': chat_id, 'text': answer}
    resp = requests.post(SEND_MESSAGE_URL,  json=post_json)
    return jsonify(resp.json()), resp.status_code


def get_status():
    led_status = query_db()
    if led_status:
        return jsonify({'led_status': led_status}), 200
    else:
        return jsonify({'led_status': 'Not content found'}), 204


@app.route('/', methods=['POST', 'GET'])
def telegram():
    if request.method == 'POST':
        post_status(request.get_json())
    if request.method == 'GET':
        get_status()
