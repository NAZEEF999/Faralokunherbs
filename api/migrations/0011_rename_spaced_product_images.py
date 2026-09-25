"""Repoint product images whose filenames contained spaces or dashes.

Vercel's static file serving 404s on files whose names contain spaces (both
raw and %20-encoded URLs). The static files were renamed to simple lowercase
names with no separators, so update any existing rows that still reference
the old spaced or dashed paths.
"""

from django.db import migrations

RENAMES = {
    '/static/img/prod/pile- plus.jpeg': '/static/img/prod/pileplus.jpeg',
    '/static/img/prod/pile-plus.jpeg':  '/static/img/prod/pileplus.jpeg',
    '/static/img/prod/herbal mixture.jpeg': '/static/img/prod/herbalmixture.jpeg',
    '/static/img/prod/herbal-mixture.jpeg': '/static/img/prod/herbalmixture.jpeg',
}


def repoint(apps, schema_editor):
    Product = apps.get_model('api', 'Product')
    for old, new in RENAMES.items():
        Product.objects.filter(local_image=old).update(local_image=new)


def revert(apps, schema_editor):
    Product = apps.get_model('api', 'Product')
    for old, new in RENAMES.items():
        Product.objects.filter(local_image=new).update(local_image=old)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_seed_phara_products'),
    ]

    operations = [
        migrations.RunPython(repoint, revert),
    ]