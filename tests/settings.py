DEBUG = True
SECRET_KEY = 'secret'

ROOT_URLCONF = 'tests.urls'

DATABASES = {
    'default': {
        'NAME': 'actrack',
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

INSTALLED_APPS = ('actrack',
                  'django_nose')

MIDDLEWARE_CLASSES = ()  # for django 1.7 not to complain!

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
