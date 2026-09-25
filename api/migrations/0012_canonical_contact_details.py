"""Set the canonical public contact/site details.

Single source of truth for contact info across the whole site:
one phone number everywhere, the business gmail, and the registered address.
"""

from django.db import migrations


def apply_contact(apps, schema_editor):
    SiteSettings = apps.get_model('api', 'SiteSettings')
    site, _ = SiteSettings.objects.get_or_create(pk=1)
    site.contact_email = 'faralokunnaturalist@gmail.com'
    site.contact_phone = '+2348030403521'
    site.contact_phone2 = ''
    site.whatsapp_number = '2348030403521'
    site.address = '3, IFESOWAPO Community'
    site.city = 'Sango Ota, Ogun State'
    site.country = 'Nigeria'
    site.save(update_fields=[
        'contact_email', 'contact_phone', 'contact_phone2', 'whatsapp_number',
        'address', 'city', 'country',
    ])


def revert_contact(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_rename_spaced_product_images'),
    ]

    operations = [
        migrations.RunPython(apply_contact, revert_contact),
    ]