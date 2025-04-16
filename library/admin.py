from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Author, AuthorProfile, Publisher, Book, Publication

# Author admin with inline profile
class AuthorProfileInline(admin.StackedInline):
    """Inline admin for author profiles"""
    model = AuthorProfile
    can_delete = False
    verbose_name = "Author Profile"
    verbose_name_plural = "Profile"

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    """Admin configuration for authors"""
    list_display = ('name', 'birth_date', 'death_date', 'book_count', 'has_profile')
    search_fields = ('name',)
    list_filter = ('birth_date',)
    date_hierarchy = 'birth_date'
    inlines = [AuthorProfileInline]

    def book_count(self, obj):
        """Count books written by this author"""
        count = obj.books.count()
        return format_html('<a href="?author__id__exact={}">{} book{}</a>',
                           obj.id, count, 's' if count != 1 else '')
    book_count.short_description = "Books"

    def has_profile(self, obj):
        """Check if author has a profile"""
        return hasattr(obj, 'profile')
    has_profile.boolean = True
    has_profile.short_description = "Has Profile"

# Book admin with inline publications
class PublicationInline(admin.TabularInline):
    """Inline admin for publications"""
    model = Publication
    extra = 1

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin configuration for books"""
    list_display = ('title', 'author', 'isbn', 'publication_date', 'display_categories')
    list_filter = ('categories', 'author', 'publication_date')
    search_fields = ('title', 'isbn', 'author__name')
    prepopulated_fields = {'slug': ('title',)}
    autocomplete_fields = ['author', 'categories']
    readonly_fields = ['display_cover']
    filter_horizontal = ('categories',)
    inlines = [PublicationInline]

    fieldsets = (
        ('Book Information', {
            'fields': ('title', 'subtitle', 'slug', 'author', 'isbn')
        }),
        ('Publishing Details', {
            'fields': ('publication_date', 'page_count')
        }),
        ('Content', {
            'fields': ('categories', 'summary')
        }),
        ('Cover', {
            'fields': ('cover', 'display_cover'),
            'classes': ('collapse',)
        }),
    )

    def display_categories(self, obj):
        """Display categories as a list"""
        return ", ".join([category.name for category in obj.categories.all()])
    display_categories.short_description = "Categories"

    def display_cover(self, obj):
        """Display book cover image"""
        if obj.cover:
            return format_html('<img src="{}" width="150" />', obj.cover.url)
        return "No cover available"
    display_cover.short_description = "Cover Preview"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin configuration for categories"""
    list_display = ('name', 'slug', 'book_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

    def book_count(self, obj):
        """Count books in this category"""
        count = obj.books.count()
        return count
    book_count.short_description = "Books"

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin configuration for publishers"""
    list_display = ('name', 'website', 'book_count')
    search_fields = ('name',)

    def book_count(self, obj):
        """Count books from this publisher"""
        return obj.books.count()
    book_count.short_description = "Books"

@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    """Admin configuration for publications"""
    list_display = ('book', 'publisher', 'publication_date', 'edition')
    list_filter = ('publisher', 'publication_date')
    search_fields = ('book__title', 'publisher__name')
    autocomplete_fields = ['book', 'publisher']