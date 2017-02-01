# CommandList
A browser-based modeless todo list built with Python 3, Flask and SQLite.

## Setup
1. `cd path/to/commandlist`
2. Optional: set up a virtual environment using virtualenv.
3. Install the required packages: `pip install -r requirements.txt`
4. Initialize the database: `python manage.py init_db`
5. Set the secret key for session encryption: `export SECRET_KEY=<your_secret_key_here>` (if you're just testing, the length of the string doesn't matter).
6. Enable or disable debug mode for the built-in server. Enable debugging with `export DEBUG=1` or disable debugging with `export DEBUG=0` (enabling debugging is recommended for testing; if you plan to run the app on a production server, though, debugging should be disabled).
7. `python run.py` (or `python3 run.py` if you have a separate Python 3 installation).

## Usage
After completing the setup steps, open a browser and navigate to `http://localhost:5000/`.

Excepting navigation links, the form at the bottom of the page is the only pint of interaction. Use it to add tasks or give commands:
- Add a task: just type it and press enter
- Delete a task: type c and its number (i.e., `c2`)
- Revise a task: type rev, its number, and the new task (i.e., `rev3 Clarify how to revise a task`)
- Start from scratch: type `reset list`

Extras tasks go in the bucket in the order they are created and only appear on the main list once the preceding tasks have been cleared.
The emphasis is on completing tasks rather than organizing lists.

