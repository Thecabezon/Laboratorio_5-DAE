# Generated by Django 5.2 on 2025-04-16 19:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('birth_date', models.DateField(blank=True, null=True)),
                ('death_date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('address', models.TextField(blank=True)),
                ('website', models.URLField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AuthorProfile',
            fields=[
                ('author', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='profile', serialize=False, to='library.author')),
                ('biography', models.TextField(blank=True)),
                ('website', models.URLField(blank=True)),
                ('photo', models.ImageField(blank=True, upload_to='authors/')),
            ],
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('subtitle', models.CharField(blank=True, max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('publication_date', models.DateField(blank=True, null=True)),
                ('isbn', models.CharField(max_length=20, unique=True, verbose_name='ISBN')),
                ('page_count', models.PositiveIntegerField(blank=True, null=True)),
                ('cover', models.ImageField(blank=True, upload_to='covers/')),
                ('summary', models.TextField(blank=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='books', to='library.author')),
                ('categories', models.ManyToManyField(related_name='books', to='library.category')),
            ],
            options={
                'ordering': ['-publication_date', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Publication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('publication_date', models.DateField()),
                ('edition', models.PositiveIntegerField(default=1)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.book')),
                ('publisher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.publisher')),
            ],
            options={
                'unique_together': {('book', 'publisher', 'edition')},
            },
        ),
        migrations.AddField(
            model_name='book',
            name='publishers',
            field=models.ManyToManyField(related_name='books', through='library.Publication', to='library.publisher'),
        ),
    ]
