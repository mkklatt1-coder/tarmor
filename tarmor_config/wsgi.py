import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tarmor_config.settings')

application = get_wsgi_application()

# Use Path to find the root folder cleanly
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

application = WhiteNoise(application, root=STATIC_ROOT)