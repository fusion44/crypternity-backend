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

Currently mixer doesn't support Django 2.0 and will fail all tests. As a workaround apply this change to mixer: https://github.com/klen/mixer/pull/90

Run _pytest --cov-report html --cov_ to run the tests.
