FLASK_PORT = 8888

# Define application directory
import os
basedir = os.path.abspath(os.path.dirname(__file__))

# Application threads
THREADS_PER_PAGE = 2

# Secret key for signing cookies
secret_key = 'landslide'

# Enable protection again(Cross-site Request Forgery)
CSRF_ENABLED = True
