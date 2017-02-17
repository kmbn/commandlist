import os
from flask import Flask
from flask_bootstrap import Bootstrap


app = Flask(__name__)
bootstrap = Bootstrap(app)


# export FLASK_CONFIG_FILE=default.cfg for default settings (no email)
app.config.from_envvar('FLASK_CONFIG_FILE')


from .views import *
from .auth import *
from .errors import *