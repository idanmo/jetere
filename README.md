# jetere
Jenkins test reports using Django

## Installation

Prepare a Python 2.7.x virtualenv and activate it.

Run:
```bash
# Clone
git clone git@github.com:idanmo/jetere.git

# Install
./install.sh

# Create a superuser
./manage.py createsuperuser

# Run the server
./manage.py runserver
```

## Configuration

* Point your browser to: http://localhost:8000/admin
* Login using superuser.
* Add a `Configuration` object with your jenkins server info.
* Create a `Job` object for each jenkins job you would like to generate test reports for.

Job object example:
* name: aaa
* jenkins_path: dir_system-tests/system-tests

## Sync with Jenkins

In order to synchronize `jetere` with jenkins, run:
```
./manage.py sync
```

Happily browse to http://localhost:8000 and view your test reports.


