from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    """Book category/genre"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Author(models.Model):
    """Book author"""
    name = models.CharField(max_length=200)
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def is_alive(self):
        """Check if author is alive"""
        return self.death_date is None

class AuthorProfile(models.Model):
    """Extended information about author (One-to-One relationship)"""
    author = models.OneToOneField(
        Author,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='profile'
    )
    biography = models.TextField(blank=True)
    website = models.URLField(blank=True)
    photo = models.ImageField(upload_to='authors/', blank=True)

    def __str__(self):
        return f"Profile for {self.author.name}"

class Publisher(models.Model):
    """Book publisher"""
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    """Book model with various relationships"""
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)
    slug = models.SlugField(unique=True)
    publication_date = models.DateField(null=True, blank=True)
    isbn = models.CharField('ISBN', max_length=20, unique=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    cover = models.ImageField(upload_to='covers/', blank=True)
    summary = models.TextField(blank=True)

    # One-to-Many relationship: One author can write many books
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='books'
    )

    # Many-to-Many relationship: A book can have multiple categories
    categories = models.ManyToManyField(
        Category,
        related_name='books'
    )

    # Many-to-Many relationship with an intermediate model
    publishers = models.ManyToManyField(
        Publisher,
        through='Publication',
        related_name='books'
    )

    class Meta:
        ordering = ['-publication_date', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Publication(models.Model):
    """Intermediate model for Book-Publisher many-to-many relationship"""
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE)
    publication_date = models.DateField()
    edition = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('book', 'publisher', 'edition')

    def __str__(self):
        return f"{self.book.title} ({self.edition}ed.) by {self.publisher.name}"