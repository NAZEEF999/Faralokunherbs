"""Seed the five PHARA herbal products (faralokun) with local static images.

Creates categories + products idempotently (update_or_create by slug), so the
same records exist locally and on the production Postgres after `migrate`.
Product images live in static/img/prod/ and ship with the deployment.
"""

from django.db import migrations


CATEGORIES = [
    {'name': 'Herbal Powders', 'slug': 'herbal-powders', 'description': 'Powdered herbal remedies for daily wellness.', 'icon_name': 'Leaf', 'sort_order': 1},
    {'name': 'Herbal Action Bitters', 'slug': 'herbal-action-bitters', 'description': 'Potent non-alcoholic herbal bitters.', 'icon_name': 'FlaskConical', 'sort_order': 2},
    {'name': 'Herbal Mixtures', 'slug': 'herbal-mixtures', 'description': 'Liquid herbal blends for chronic conditions.', 'icon_name': 'Droplet', 'sort_order': 3},
    {'name': 'Herbal Balms', 'slug': 'herbal-balms', 'description': 'Topical balms for fast relief.', 'icon_name': 'Flower2', 'sort_order': 4},
]

PRODUCTS = [
    {
        'slug': 'phara-okcoba-herbal-powder',
        'title': 'PHARA OKCOBA Herbal Powder',
        'category': 'Herbal Powders',
        'short_description': '100% natural herbal powder that gives fast relief from malaria, yellow fever, headache, dizziness, cold and fever. Suitable for men, women and children.',
        'description': 'PHARA OKCOBA is a powerful herbal powder made from carefully selected natural ingredients including Neem Leaf, Bitter Leaf, Andrographis, Ginger, Garlic, Lemon Grass, Guava Leaf, Turmeric and Clove. It is specially formulated to treat and prevent malaria recurrence, help manage yellow fever symptoms, relieve dizziness, headache, body pain, cold, fever and flu. It also boosts immunity and energy. 100% natural, safe and effective for the whole family.',
        'ingredients': 'Neem Leaf\nBitter Leaf\nAndrographis\nGinger\nGarlic\nLemon Grass\nGuava Leaf\nTurmeric\nClove',
        'benefits': 'Treats and prevents malaria recurrence\nHelps manage yellow fever symptoms\nRelieves dizziness, headache and body pain\nRelieves cold, fever and flu\nBoosts immunity and energy',
        'local_image': '/static/img/prod/okcoba.jpeg',
        'sort_order': 1,
    },
    {
        'slug': 'phara-dagboru-herbal-action-bitters',
        'title': 'PHARA DAGBORU Herbal Action Bitters',
        'category': 'Herbal Action Bitters',
        'short_description': 'Non-alcoholic herbal bitters designed to boost man power, sexual vitality, stamina, sperm count and overall male wellness. Also helps with stress and performance anxiety.',
        'description': 'PHARA DAGBORU is a potent non-alcoholic herbal action bitters formulated for man power and total wellness. It helps improve sexual drive and performance, enhance erection and stamina, relieve stress, anxiety and depression, reduce performance anxiety, treat weak erection and premature ejaculation, increase libido, improve sperm count and motility, and boost energy and endurance. Key ingredients include Ginger, Ginseng, Horny Goat Weed, Maca Root, Tribulus Terrestris, Guarana, Tongkat Ali, Clove, African Yohimbe and Damiana Leaf. Suitable for men of all ages and couples.',
        'ingredients': 'Ginger\nGinseng\nHorny Goat Weed\nMaca Root\nTribulus Terrestris\nGuarana\nTongkat Ali\nClove\nAfrican Yohimbe\nDamiana Leaf',
        'benefits': 'Boosts libido and sexual drive\nImproves erection and stamina\nIncreases sperm count and motility\nRelieves stress, anxiety and performance anxiety\nBoosts energy and endurance',
        'local_image': '/static/img/prod/dagboru.jpeg',
        'sort_order': 2,
    },
    {
        'slug': 'phara-pile-plus-herbal-powder',
        'title': 'PHARA PILE PLUS Herbal Powder',
        'category': 'Herbal Powders',
        'short_description': 'Natural herbal powder that effectively treats piles, infections, urinary tract infection, menstrual pain, running stomach and also supports man power and weight reduction.',
        'description': 'PHARA PILE PLUS is a 100% natural herbal powder that provides complete relief from piles (hemorrhoids). It shrinks piles naturally, relieves pain, swelling and itching, treats infections and prevents recurrence, detoxifies the body, helps burn fat and reduce pot belly, eases menstrual pain and disorders, stops running stomach, and supports man power, energy and stamina. Main ingredients include Senna Leaves, Neem Leaves, Aloe Vera, Ginger, Garlic, Turmeric and Cloves. Safe and effective for both men and women.',
        'ingredients': 'Senna Leaves\nNeem Leaves\nAloe Vera\nGinger\nGarlic\nTurmeric\nCloves',
        'benefits': 'Shrinks piles naturally\nRelieves pain, swelling and itching\nTreats infections and prevents recurrence\nDetoxifies the body and helps burn fat\nEases menstrual pain and running stomach\nSupports man power, energy and stamina',
        'local_image': '/static/img/prod/pileplus.jpeg',
        'sort_order': 3,
    },
    {
        'slug': 'phara-faralokun-herbal-mixture',
        'title': 'PHARA FARALOKUN Herbal Mixture',
        'category': 'Herbal Mixtures',
        'short_description': 'Non-alcoholic herbal mixture that treats chronic piles, anus pulling, hemorrhoids, menstrual pains and also boosts immunity and man power.',
        'description': 'PHARA FARALOKUN is a non-alcoholic herbal mixture specially formulated for natural relief from chronic piles, anus pulling, irritation and hemorrhoids. It helps shrink swollen veins, relieve pain and discomfort, boost the immune system, enhance man power and stamina, and ease menstrual cramps and pains. Powerful natural ingredients include Aloe Vera, Neem Leaf, Ginger, Garlic, Clove, Herbal Leaves, Honey, Turmeric and Aframomum. Suitable for both men and women. 100% natural, safe and effective.',
        'ingredients': 'Aloe Vera\nNeem Leaf\nGinger\nGarlic\nClove\nHerbal Leaves\nHoney\nTurmeric\nAframomum',
        'benefits': 'Relieves chronic piles and hemorrhoids\nShrinks swollen veins and irritation\nBoosts the immune system\nEnhances man power and stamina\nEases menstrual cramps and pains',
        'local_image': '/static/img/prod/herbalmixture.jpeg',
        'sort_order': 4,
    },
    {
        'slug': 'phara-magic-herbal-balm',
        'title': 'PHARA MAGIC Herbal Balm',
        'category': 'Herbal Balms',
        'short_description': 'Fast-acting natural herbal balm that relieves headache, body ache, cold, cough, joint pain, back pain, chest congestion and stiff neck. Safe for all ages.',
        'description': 'PHARA MAGIC is a gentle yet powerful herbal balm that provides fast relief from headache and migraine, body and muscular aches, cold, cough and catarrh, joint pains, sprains and strains, lower back pain, chest congestion and stiff neck. It opens the chest, eases breathing and gives comfort and relaxation. Key natural ingredients include Eucalyptus, Menthol, Camphor, Clove Oil, Peppermint, Ginger, Lavender, Olive Oil and Tea Tree Oil. Suitable for men, women and children of all ages. 100% natural, safe and effective with no side effects.',
        'ingredients': 'Eucalyptus\nMenthol\nCamphor\nClove Oil\nPeppermint\nGinger\nLavender\nOlive Oil\nTea Tree Oil',
        'benefits': 'Relieves headache and migraine\nSoothes body and muscular aches\nClears cold, cough and catarrh\nEases joint pains, back pain and stiff neck\nOpens the chest and eases breathing',
        'local_image': '/static/img/prod/phara.jpeg',
        'sort_order': 5,
    },
]


def seed(apps, schema_editor):
    ProductCategory = apps.get_model('api', 'ProductCategory')
    Product = apps.get_model('api', 'Product')

    for cat in CATEGORIES:
        ProductCategory.objects.update_or_create(
            name=cat['name'],
            defaults={k: v for k, v in cat.items() if k != 'name'},
        )

    for prod in PRODUCTS:
        cat = ProductCategory.objects.filter(name=prod['category']).first()
        defaults = {
            'title': prod['title'],
            'short_description': prod['short_description'],
            'description': prod['description'],
            'ingredients': prod.get('ingredients', ''),
            'benefits': prod.get('benefits', ''),
            'local_image': prod['local_image'],
            'category': cat,
            'price': 0,
            'track_stock': False,
            'stock_quantity': 0,
            'is_featured': True,
            'active': True,
            'sort_order': prod['sort_order'],
        }
        Product.objects.update_or_create(slug=prod['slug'], defaults=defaults)


def unseed(apps, schema_editor):
    Product = apps.get_model('api', 'Product')
    Product.objects.filter(slug__in=[p['slug'] for p in PRODUCTS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_product_local_image'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]