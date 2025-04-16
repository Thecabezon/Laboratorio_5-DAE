from django.db import models
from django.core.validators import MinValueValidator
from library.models import Book
from django.urls import reverse

class Shelf(models.Model):
    """Modelo para estanterías de la biblioteca"""
    name = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Capacidad máxima de libros en esta estantería"
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Shelves'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.location})"

    def get_absolute_url(self):
        return reverse('inventory:shelf-detail', kwargs={'pk': self.pk})

    @property
    def available_space(self):
        used_space = sum(item.quantity for item in self.items.all())
        return self.capacity - used_space

class InventoryItem(models.Model):
    """Modelo para items en inventario"""
    CONDITION_CHOICES = [
        ('NEW', 'Nuevo'),
        ('GOOD', 'Bueno'),
        ('FAIR', 'Regular'),
        ('POOR', 'Malo'),
        ('DAMAGED', 'Dañado')
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='inventory_items'
    )
    shelf = models.ForeignKey(
        Shelf,
        on_delete=models.SET_NULL,
        null=True,
        related_name='items'
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )
    minimum_quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(0)]
    )
    condition = models.CharField(
        max_length=10,
        choices=CONDITION_CHOICES,
        default='GOOD'
    )
    notes = models.TextField(blank=True)
    last_checked = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['book__title']
        unique_together = ['book', 'shelf', 'condition']

    def __str__(self):
        return f"{self.book.title} - {self.quantity} unidades"

    @property
    def needs_restock(self):
        return self.quantity <= self.minimum_quantity

class Acquisition(models.Model):
    """Modelo para registro de adquisiciones"""
    ACQUISITION_TYPES = [
        ('PURCHASE', 'Compra'),
        ('DONATION', 'Donación'),
        ('EXCHANGE', 'Intercambio')
    ]

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='acquisitions'
    )
    quantity = models.PositiveIntegerField()
    acquisition_type = models.CharField(
        max_length=10,
        choices=ACQUISITION_TYPES
    )
    date_acquired = models.DateField(auto_now_add=True)
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    supplier = models.CharField(max_length=100, blank=True)
    invoice_number = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.book.title} - {self.quantity} unidades ({self.get_acquisition_type_display()})"