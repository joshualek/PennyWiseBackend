# migrations/000X_create_initial_categories.py

from django.db import migrations, models

def create_categories(apps, schema_editor):
    Category = apps.get_model('api', 'Category')
    categories = [
        {'id': 1, 'name': 'Food'},
        {'id': 2, 'name': 'Transport'},
        {'id': 3, 'name': 'Shopping'},
        {'id': 4, 'name': 'Others'},
    ]
    for category_data in categories:
        Category.objects.update_or_create(id=category_data['id'], defaults={'name': category_data['name']})

class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),  # Replace with the actual name of the previous migration
    ]

    operations = [
        migrations.RunPython(create_categories),
    ]