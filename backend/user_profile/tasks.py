"""
Contains all recurring tasks relevant to the user.
This includes:
* Calculating user's net worth
* Calculating data necessary for the charts shown in UI
* Scheduling scans for new trades in his exchange and wallet accounts
* ...
"""
from backend.celery import app


@app.task
def test(arg):
    """Test task"""
    print(arg)
