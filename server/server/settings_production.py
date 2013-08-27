# Settings for Piconga production server
#
# This uses one of the recommended ways for setting up a minimal delta
# configuration from the base (debug) settings by importing all the settings
# and overriding the ones that need to change.

# Import base settings.  Yup - this approach is straight from Chapter 12 of the
# django book.
from settings import *

# No debug features please!
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Use postgres for the live back-end DB.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'piconga',
        'USER': 'piconga',
        'PASSWORD': 'piconga',
        'HOST': '',
        'PORT': '',
    }
}
