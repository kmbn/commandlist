import os
from flask import Flask
from flask_bootstrap import Bootstrap


app = Flask(__name__)
bootstrap = Bootstrap(app)


# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'commandlist.db')
    ))


# Set SECRET_KEY in environment
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'secret_key'