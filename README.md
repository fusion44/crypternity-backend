# Crypternity Backend

### Setup

[Virtualenvwrapper](http://virtualenvwrapper.readthedocs.io/en/latest/install.html) must be working properly on your system before continuing.

* clone the repository
* add a new virtual environment: _mkvirtualenv crypternity_
* _pip install -r requirements.txt_
* deactivate virtual environment to prevent some errors _deactivate_
* use the environment: _workon crypternity_
* _./manage.py makemigrations_
* _./manage.py migrate_

### Testing

Run _pytest --cov-report html --cov_ to run the tests.

Alternatively, run tests and open the results coverage html page with Google Chrome: _pytest --cov-report html --cov && google-chrome-stable ./htmlcov/index.html_
