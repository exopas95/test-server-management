#!flask/bin/python

from config import FLASK_PORT, secret_key
from app import app

app.secret_key = secret_key
app.run(debug = True, host = '0.0.0.0', port = int(FLASK_PORT), threaded=True, use_reloader=True)
