from django.contrib import admin
from django.utils.html import format_html
from .models import Shelf, InventoryItem, Acquisition

@admin.register(Shelf)
class ShelfAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'capacity', 'available_space',
                   'is_active')
    list_filter = ('is_active', 'location')
    search_fields = ('name', 'location')
    ordering = ('name',)

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('book', 'shelf', 'quantity', 'condition',
                   'stock_status', 'last_checked')
    list_filter = ('condition', 'shelf', 'last_checked')
    search_fields = ('book__title', 'shelf__name')
    ordering = ('book__title',)

    def stock_status(self, obj):
        if obj.needs_restock:
            return format_html(
                '<span style="color: red;">Necesita Reposición</span>'
            )
        return format_html(
            '<span style="color: green;">OK</span>'
        )
    stock_status.short_description = 'Estado del Stock'

@admin.register(Acquisition)
class AcquisitionAdmin(admin.ModelAdmin):
    list_display = ('book', 'quantity', 'acquisition_type',
                   'date_acquired', 'cost')
    list_filter = ('acquisition_type', 'date_acquired')
    search_fields = ('book__title', 'supplier', 'invoice_number')
    ordering = ('-date_acquired',)