# !Currently unmaintained!

## Crypternity Backend

### Setup

[Virtualenvwrapper](http://virtualenvwrapper.readthedocs.io/en/latest/install.html) must be working properly on your system before continuing.

* clone the repository
* add a new virtual environment: _mkvirtualenv crypternity_
* _pip install -r requirements.txt_
* deactivate virtual environment to prevent some errors _deactivate_
* use the environment: _workon crypternity_
* _./manage.py makemigrations_
* _./manage.py migrate_
* copy config.ini.sample to config.ini and change the secret key and database password. The secret key should be a long string of random letters and numbers.

#### RabbitMQ

A RabbitMQ server or a Redis instance for [Celery](http://www.celeryproject.org/) is necessary. Easiest way to run RabbitMQ is using a Raspberry Pi with [HypriotOS](https://blog.hypriot.com/downloads/). Hypriot comes with everything necessary to run the necessary Docker Images:

On the RPi:

* mkdir rabbitmqdata && mkdir rabbitmqlogs
* _docker pull ronnyroos/rpi-rabbitmq_
* _docker run --restart=unless-stopped -d -p 5672:5672 -p 15672:15672 -v /home/pirate/rabbitmqlogs:/data/log -v /home/pirate/rabbitmqdata:/data/mnesia ronnyroos/rpi-rabbitmq_

On the dev machine, open config.ini and find the following line:

```config
celery_broker_url = amqp://192.168.178.108//
```

Replace the ip with your server ip

Run Celery Beat (task scheduler):

* _celery -A backend beat -l debug --scheduler django_celery_beat.schedulers:DatabaseScheduler_

Finally, run Celery:

* _celery worker -A backend --loglevel=debug --concurrency=4_

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
