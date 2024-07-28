# this is a script to manually load the student discount messages 
# from the json file into the database

import os
import django

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Initialize Django
django.setup()

from api.models import StudentDiscount

StudentDiscount.load_messages_from_json()