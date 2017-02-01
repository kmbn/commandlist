from config import app
from errors import internal_server_error, page_not_found
from views import *


# Run app
if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])