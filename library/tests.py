from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Author, Book, Category, Publisher, Publication

class AuthorModelTest(TestCase):
    """Test cases for the Author model"""

    def setUp(self):
        """Create test author"""
        self.author = Author.objects.create(
            name="J.K. Rowling",
            birth_date="1965-07-31"
        )

    def test_author_creation(self):
        """Test author creation and string representation"""
        self.assertEqual(str(self.author), "J.K. Rowling")
        self.assertEqual(self.author.name, "J.K. Rowling")
        self.assertTrue(self.author.is_alive)

class BookModelTest(TestCase):
    """Test cases for the Book model"""

    def setUp(self):
        """Create test book and related objects"""
        self.author = Author.objects.create(
            name="George Orwell",
            birth_date="1903-06-25",
            death_date="1950-01-21"
        )
        self.category = Category.objects.create(
            name="Dystopian",
            description="Dystopian fiction"
        )
        self.book = Book.objects.create(
            title="1984",
            author=self.author,
            isbn="9780451524935",
            publication_date="1949-06-08",
            summary="A dystopian novel set in Airstrip One"
        )
        self.book.categories.add(self.category)

    def test_book_creation(self):
        """Test book creation and relationships"""
        self.assertEqual(str(self.book), "1984")
        self.assertEqual(self.book.author.name, "George Orwell")
        self.assertEqual(self.book.categories.first().name, "Dystopian")
        self.assertEqual(self.book.slug, "1984")

class AdminAccessTest(TestCase):
    """Test cases for admin access"""

    def setUp(self):
        """Create admin user"""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        self.client.login(username='admin', password='adminpassword')

    def test_admin_access(self):
        """Test admin site accessibility"""
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)

    def test_model_admin_access(self):
        """Test access to model admin pages"""
        models = ['author', 'book', 'category', 'publisher', 'publication']
        for model in models:
            response = self.client.get(reverse(f'admin:library_{model}_changelist'))
            self.assertEqual(response.status_code, 200)