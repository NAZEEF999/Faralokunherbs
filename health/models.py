from django.db import models
from django.utils.text import slugify
from cloudinary.models import CloudinaryField


def _lines(text):
    return [line.strip() for line in (text or '').splitlines() if line.strip()]


# ── ANATOMY ──────────────────────────────────────────────────────────────────
class AnatomyTopic(models.Model):
    """
    An explorable body part/system entry, e.g. "Femur" under the Skeletal
    System. Grouped by a fixed `system` taxonomy rather than a separate
    manageable model -- unlike product categories, this list doesn't need
    to grow arbitrarily, so one model keeps the CRUD surface much smaller.
    """
    SYSTEM_CHOICES = [
        ('skeletal',     'Skeletal System'),
        ('muscular',     'Muscular System'),
        ('circulatory',  'Circulatory System'),
        ('digestive',    'Digestive System'),
        ('nervous',      'Nervous System'),
        ('respiratory',  'Respiratory System'),
        ('organs',       'Organs'),
        ('other',        'Other'),
    ]

    system             = models.CharField(max_length=30, choices=SYSTEM_CHOICES, default='skeletal')
    name               = models.CharField(max_length=150)
    slug               = models.SlugField(unique=True, blank=True)
    image              = CloudinaryField('image', folder='phara/health/anatomy', blank=True, null=True)
    short_description  = models.CharField(max_length=300)
    function           = models.TextField(blank=True, help_text='What this part does.')
    common_issues      = models.TextField(blank=True, help_text='Common problems/conditions, one per line.')
    general_info       = models.TextField(blank=True, help_text='Further educational information.')
    sort_order         = models.PositiveIntegerField(default=0)
    is_active          = models.BooleanField(default=True)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['system', 'sort_order', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_system_display()})'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def common_issue_list(self):
        return _lines(self.common_issues)


# ── HEALTH CONDITIONS ────────────────────────────────────────────────────────
class HealthCondition(models.Model):
    name             = models.CharField(max_length=150)
    slug             = models.SlugField(unique=True, blank=True)
    image            = CloudinaryField('image', folder='phara/health/conditions', blank=True, null=True)
    overview         = models.TextField()
    causes           = models.TextField(blank=True, help_text='Causes / risk factors, one per line.')
    symptoms         = models.TextField(blank=True, help_text='One per line.')
    prevention       = models.TextField(blank=True, help_text='One per line.')
    lifestyle_tips   = models.TextField(blank=True, help_text='One per line.')
    treatment_info   = models.TextField(
        blank=True, help_text='General educational information — not a prescription or diagnosis.')
    seek_care_info   = models.TextField(
        blank=True, help_text='When to seek professional medical attention.')
    related_herbs    = models.ManyToManyField('health.Herb', blank=True, related_name='related_conditions')
    is_featured      = models.BooleanField(default=False)
    is_active        = models.BooleanField(default=True)
    sort_order       = models.PositiveIntegerField(default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def cause_list(self):
        return _lines(self.causes)

    @property
    def symptom_list(self):
        return _lines(self.symptoms)

    @property
    def prevention_list(self):
        return _lines(self.prevention)

    @property
    def lifestyle_list(self):
        return _lines(self.lifestyle_tips)


# ── HERBS & INGREDIENTS ──────────────────────────────────────────────────────
class Herb(models.Model):
    common_name         = models.CharField(max_length=150)
    scientific_name      = models.CharField(max_length=150, blank=True)
    slug                 = models.SlugField(unique=True, blank=True)
    image                = CloudinaryField('image', folder='phara/health/herbs', blank=True, null=True)
    description          = models.TextField()
    traditional_uses     = models.TextField(blank=True, help_text='One per line.')
    compounds_info       = models.TextField(
        blank=True, help_text='Active compounds / nutrients — educational, not a health claim.')
    preparation_info     = models.TextField(blank=True, help_text='How it is typically prepared or used.')
    safety_info          = models.TextField(blank=True)
    interactions_info    = models.TextField(blank=True, help_text='Possible interactions with medications, etc.')
    precautions          = models.TextField(blank=True)
    related_products     = models.ManyToManyField('api.Product', blank=True, related_name='related_herbs')
    is_featured          = models.BooleanField(default=False)
    is_active            = models.BooleanField(default=True)
    sort_order           = models.PositiveIntegerField(default=0)
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', 'common_name']

    def __str__(self):
        return self.common_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.common_name)
        super().save(*args, **kwargs)

    @property
    def traditional_use_list(self):
        return _lines(self.traditional_uses)
