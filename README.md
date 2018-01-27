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

#### Debugging using VS code

* Install the Visual Studio code [Python extension](https://code.visualstudio.com/docs/languages/python)
* Open workspace settings and set the appropriate python path for the virtual env

```json
{
  "python.pythonPath": "/home/fusion44/.virtualenvs/crypternity/bin/python3.6"
}
```

* Select _Python: Django_ as DEBUG configuration

### Testing

Run _pytest --cov-report html --cov_ to run the tests.

Alternatively, run tests and open the results coverage html page with Google Chrome: _pytest --cov-report html --cov && google-chrome-stable ./htmlcov/index.html_

```

```
