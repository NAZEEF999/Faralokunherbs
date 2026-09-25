"""Seed the health library and services with the site's new content and images.

Adds:
- 4 services (Herbal Medicine, Dietary Healing, Spiritual Healing, Wellness & Detox)
  mapped to their recommended images from static/img/health/
- 2 Wellness blog posts (Herbal Tea Ritual, Nourishing Healthy Bowl)
- 3 health conditions (Digestive Discomfort, Headache & Tension, Respiratory Calm)
- 3 herbs (Fresh Medicinal Herbs, Ginger/Turmeric/Garlic, Dried Herbs & Powder)
- 4 anatomy topics (Digestive System, Heart, Liver, Kidney)

Images are served locally from /static/img/health/ so they work on Vercel
without Cloudinary uploads. Filenames contain no spaces (Vercel requirement).
"""
from django.db import migrations

IMG = '/static/img/health'

SERVICES = [
    {
        'title': 'Herbal Medicine Consultation',
        'slug': 'herbal-medicine-consultation',
        'short_description': ('One-on-one consultation on traditional herbal '
                              'formulations and how they may support your wellness goals.'),
        'description': ('Sit down with our herbalist to discuss your health goals and '
                        'learn how traditional herbal preparations may support your '
                        'wellness journey. Every recommendation is educational and '
                        'personalised to your needs.'),
        'category': 'herbal_medicine',
        'image': f'{IMG}/JFl7u.jpg',
        'is_featured': True,
    },
    {
        'title': 'Dietary Healing & Nutrition',
        'slug': 'dietary-healing-nutrition',
        'short_description': ('Whole-food nutrition guidance that works alongside herbal '
                              'care to support energy, digestion and vitality.'),
        'description': ('A balanced plate of fresh fruits, vegetables and healthy fats is '
                        'the foundation of wellness. We share practical nutrition guidance '
                        'that complements your herbal care routine for long-term health.'),
        'category': 'dietary_healing',
        'image': f'{IMG}/AEV2E.jpg',
        'is_featured': True,
    },
    {
        'title': 'Spiritual Healing',
        'slug': 'spiritual-healing',
        'short_description': ('Calm, prayer-based healing sessions focused on inner peace '
                              'and whole-body wellness.'),
        'description': ('A serene session centred on relaxation, reflection and spiritual '
                        'balance. Natural breathing and a peaceful setting help restore '
                        'calm and support emotional and physical wellbeing.'),
        'category': 'spiritual_healing',
        'image': f'{IMG}/HTzUR.jpg',
        'is_featured': True,
    },
    {
        'title': 'Wellness & Detox Support',
        'slug': 'wellness-detox-support',
        'short_description': ('Guidance for gentle, natural detox and internal body support '
                              'using traditional practices.'),
        'description': ('Support your body\'s natural detoxification with traditional '
                        'herbal care and lifestyle guidance focused on the organs that '
                        'keep you balanced — liver, kidneys and digestion.'),
        'category': 'other',
        'image': f'{IMG}/liver.jpg',
        'is_featured': True,
    },
]

BLOG_POSTS = [
    {
        'title': 'Herbal Tea Ritual',
        'slug': 'herbal-tea-ritual',
        'excerpt': ('The calming practice of preparing and enjoying herbal tea as a daily '
                    'self-care ritual.'),
        'content': ('Herbal tea is one of the simplest and most effective ways to take '
                    'medicinal plants. A warm cup of properly prepared herbal infusion '
                    'supports relaxation, digestion, and daily wellness while creating a '
                    'mindful self-care moment.'),
        'category': 'Wellness',
        'image': f'{IMG}/qLDdj.jpg',
    },
    {
        'title': 'Nourishing Healthy Bowl',
        'slug': 'nourishing-healthy-bowl',
        'excerpt': ('Vibrant whole foods that support energy and vitality.'),
        'content': ('A balanced plate of fresh fruits, vegetables, and healthy fats '
                    'provides the body with essential nutrients. Proper nutrition forms '
                    'the foundation of wellness and works hand-in-hand with herbal support '
                    'for long-term health.'),
        'category': 'Wellness',
        'image': f'{IMG}/AEV2E.jpg',
    },
]

CONDITIONS = [
    {
        'name': 'Digestive Discomfort',
        'slug': 'digestive-discomfort',
        'overview': ('Digestive issues such as bloating, stomach pain, and indigestion are '
                     'among the most common health complaints. This image represents the '
                     'body\'s natural way of indicating when the digestive system needs '
                     'attention and support through diet, herbs, and lifestyle changes.'),
        'image': f'{IMG}/AhcYq.jpg',
    },
    {
        'name': 'Headache & Tension',
        'slug': 'headache-tension',
        'overview': ('Headaches and migraines can result from stress, dehydration, poor '
                     'posture, or internal imbalances. This image illustrates the common '
                     'experience of head tension and highlights the importance of '
                     'identifying root causes for lasting relief.'),
        'image': f'{IMG}/gJERA.jpg',
    },
    {
        'name': 'Respiratory Calm & Breathing',
        'slug': 'respiratory-calm-breathing',
        'overview': ('Healthy respiration is essential for overall vitality. This image '
                     'represents calm, clear breathing and the role of natural support in '
                     'maintaining respiratory comfort, especially during seasonal changes '
                     'or mild congestion.'),
        'image': f'{IMG}/HTzUR.jpg',
    },
]

HERBS = [
    {
        'common_name': 'Fresh Medicinal Herbs',
        'slug': 'fresh-medicinal-herbs',
        'description': ('Fresh herbs such as mint, basil, thyme, and neem-type leaves have '
                        'been used for generations in traditional healing. They are valued '
                        'for their natural compounds that support digestion, immunity, and '
                        'overall wellness when prepared correctly.'),
        'image': f'{IMG}/JFl7u.jpg',
    },
    {
        'common_name': 'Ginger, Turmeric & Garlic',
        'slug': 'ginger-turmeric-garlic',
        'description': ('Ginger, turmeric, and garlic are among the most researched natural '
                        'ingredients. They are widely used to support immunity, reduce '
                        'inflammation, aid digestion, and promote general health in both '
                        'traditional and modern herbal practices.'),
        'image': f'{IMG}/eJyYh.jpg',
    },
    {
        'common_name': 'Dried Herbs & Herbal Powder',
        'slug': 'dried-herbs-herbal-powder',
        'description': ('Drying and powdering herbs helps preserve their active compounds '
                        'for longer use. This form is commonly used in herbal mixtures, '
                        'teas, and traditional remedies to deliver concentrated natural '
                        'support.'),
        'image': f'{IMG}/XYSEK.jpg',
    },
]

ANATOMY = [
    {
        'name': 'Digestive System',
        'slug': 'digestive-system',
        'system': 'digestive',
        'short_description': ('Overview of the human digestive system and how food is '
                              'processed in the body.'),
        'function': ('The digestive system is responsible for breaking down food, '
                     'absorbing nutrients, and eliminating waste. It includes the mouth, '
                     'esophagus, stomach, intestines, liver, pancreas, and related organs. '
                     'Understanding how this system works helps in supporting better '
                     'digestion and overall gut health through proper diet and herbal care.'),
        'image': f'{IMG}/digestivesystem.jpg',
    },
    {
        'name': 'Heart',
        'slug': 'heart',
        'system': 'circulatory',
        'short_description': ('The human heart and its role in circulating blood '
                              'throughout the body.'),
        'function': ('The heart is a vital muscular organ that pumps blood to supply '
                     'oxygen and nutrients to every part of the body. A healthy heart '
                     'supports energy, circulation, and overall vitality. Lifestyle, diet, '
                     'and natural support play important roles in maintaining good '
                     'cardiovascular health.'),
        'image': f'{IMG}/heart.jpg',
    },
    {
        'name': 'Liver',
        'slug': 'liver',
        'system': 'organs',
        'short_description': ('The liver and its essential functions in detoxification '
                              'and metabolism.'),
        'function': ('The liver is one of the body\'s most important organs. It filters '
                     'toxins, processes nutrients, produces bile, and supports metabolism. '
                     'A healthy liver is key to energy, digestion, and overall wellness. '
                     'Many traditional herbs are used to support and protect liver function.'),
        'image': f'{IMG}/liver.jpg',
    },
    {
        'name': 'Kidney',
        'slug': 'kidney',
        'system': 'organs',
        'short_description': ('The kidneys and their role in filtering blood and '
                              'maintaining body balance.'),
        'function': ('The kidneys filter waste products from the blood, regulate fluid '
                     'balance, and help control blood pressure. Healthy kidney function is '
                     'essential for removing toxins and maintaining internal balance. '
                     'Proper hydration and supportive natural practices help keep the '
                     'kidneys working well.'),
        'image': f'{IMG}/Kidney.jpg',
    },
]


def seed_health_and_services(apps, schema_editor):
    Service = apps.get_model('api', 'Service')
    BlogPost = apps.get_model('api', 'BlogPost')
    HealthCondition = apps.get_model('health', 'HealthCondition')
    Herb = apps.get_model('health', 'Herb')
    AnatomyTopic = apps.get_model('health', 'AnatomyTopic')

    for i, item in enumerate(SERVICES):
        Service.objects.get_or_create(
            slug=item['slug'],
            defaults={
                'title': item['title'],
                'short_description': item['short_description'],
                'description': item['description'],
                'category': item['category'],
                'local_image': item['image'],
                'is_featured': item['is_featured'],
                'active': True,
                'duration_minutes': 60,
                'price': 0,
                'sort_order': i,
            },
        )

    for i, item in enumerate(BLOG_POSTS):
        BlogPost.objects.get_or_create(
            slug=item['slug'],
            defaults={
                'title': item['title'],
                'excerpt': item['excerpt'],
                'content': item['content'],
                'category': item['category'],
                'local_image': item['image'],
                'is_published': True,
            },
        )

    for i, item in enumerate(CONDITIONS):
        HealthCondition.objects.get_or_create(
            slug=item['slug'],
            defaults={
                'name': item['name'],
                'overview': item['overview'],
                'local_image': item['image'],
                'is_featured': True,
                'is_active': True,
                'sort_order': i,
            },
        )

    for i, item in enumerate(HERBS):
        Herb.objects.get_or_create(
            slug=item['slug'],
            defaults={
                'common_name': item['common_name'],
                'description': item['description'],
                'local_image': item['image'],
                'is_featured': True,
                'is_active': True,
                'sort_order': i,
            },
        )

    for i, item in enumerate(ANATOMY):
        AnatomyTopic.objects.get_or_create(
            slug=item['slug'],
            defaults={
                'name': item['name'],
                'system': item['system'],
                'short_description': item['short_description'],
                'function': item['function'],
                'local_image': item['image'],
                'is_active': True,
                'sort_order': i,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_blogpost_local_image_service_local_image'),
        ('health', '0002_anatomytopic_local_image_healthcondition_local_image_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_health_and_services, migrations.RunPython.noop),
    ]