DEBUG = True
ENV_NAME = '%(name)s'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.%(db_engine)s', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '%(db_name)s',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
