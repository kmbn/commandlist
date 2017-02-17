import os
from flask import Flask
from flask_bootstrap import Bootstrap


app = Flask(__name__)
bootstrap = Bootstrap(app)


app.config['DATABASE'] = os.path.join(app.root_path, 'commandlist.db')
app.config['DEBUG'] = int(os.environ.get('DEBUG'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


from .views import *
from .auth import *
from .errors import *