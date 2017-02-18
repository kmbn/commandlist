import os
from flask import Flask
from flask_bootstrap import Bootstrap
from passlib.context import CryptContext


app = Flask(__name__)
bootstrap = Bootstrap(app)


# export FLASK_CONFIG_FILE=default.cfg for default settings (no email)
app.config.from_envvar('FLASK_CONFIG_FILE')


# Passlib config:
pwd_context = CryptContext(
    # Replace this list with the hash(es) you wish to support.
    # The first hash will be the default
    schemes=["pbkdf2_sha256"]
    # Optionally, set the number of rounds that should be used.
    # Leaving this alone is usually safe, and will use passlib's defaults.
    ## pbkdf2_sha256__rounds = 29000,
    )


from .views import *
from .auth import *
from .errors import *