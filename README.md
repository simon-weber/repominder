# Repominder

Repominder is a Django project that reminds OSS maintainers when they've forgotten to cut a release.

You can use it at [https://www.repominder.com](https://www.repominder.com).

## project layout

* repominder/apps/core: main django app
* repominder/lib: non-django code
* ops: ansible config (3rd party roles vendorized)
* secrets: prod secrets (managed with transcypt)
* assets: served with dj-static (not nginx because I'm lazy)

## development

To create a new dev environment:

* create a new virtualenv
* `pip install -r dev-requirements.txt`
* `DJANGO_SETTINGS_MODULE=repominder.settings_dev python manage.py migrate`

Then:

* run locally: `DJANGO_SETTINGS_MODULE=repominder.settings_dev python manage.py runserver`
