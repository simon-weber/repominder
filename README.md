# Repominder

Repominder is a Django project that reminds OSS maintainers when they've forgotten to cut a release.

You can use it at [https://www.repominder.com](https://www.repominder.com).

## development

To create a new dev environment:

* create a new python 3 virtualenv
* `pip install -r dev-requirements.txt`
* `DJANGO_SETTINGS_MODULE=repominder.settings_dev python manage.py migrate`

Then:

* run locally: `DJANGO_SETTINGS_MODULE=repominder.settings_dev python manage.py runserver`
