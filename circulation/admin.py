from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Member, BookCopy, Loan, Reservation, Fee


class FeeInline(admin.TabularInline):
    """Inline admin for fees"""
    model = Fee
    extra = 0
    fields = ('fee_type', 'amount', 'status', 'date_assessed', 'date_paid')
    readonly_fields = ('date_assessed',)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin configuration for members"""
    list_display = ('full_name', 'email', 'membership_type', 'membership_date', 
                    'membership_status', 'active_loans', 'total_fees')
    list_filter = ('is_active', 'membership_type', 'membership_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    date_hierarchy = 'membership_date'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_active')
        }),
        ('Contact Details', {
            'fields': ('address', 'phone_number')
        }),
        ('Membership', {
            'fields': ('membership_type', 'membership_date', 'membership_expiry')
        }),
    )
    
    def membership_status(self, obj):
        """Display membership status with color coding"""
        if obj.is_active and obj.is_membership_valid:
            return format_html('<span style="color: green;">Active</span>')
        elif not obj.is_active:
            return format_html('<span style="color: red;">Inactive</span>')
        else:
            return format_html('<span style="color: orange;">Expired</span>')
    membership_status.short_description = "Status"
    
    def active_loans(self, obj):
        """Display active loans with link to filtered loan list"""
        count = obj.active_loans_count
        url = reverse('admin:circulation_loan_changelist') + f'?member__id__exact={obj.id}&status__exact=AC'
        return format_html('<a href="{}">{}</a>', url, count)
    active_loans.short_description = "Active Loans"
    
    def total_fees(self, obj):
        """Display total outstanding fees"""
        total = Fee.objects.filter(
            loan__member=obj, 
            status='OU'
        ).values_list('amount', flat=True)
        
        if not total:
            return "$0.00"
            
        total_sum = sum(total)
        return f"${total_sum:.2f}"
    total_fees.short_description = "Outstanding Fees"


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
    """Admin configuration for book copies"""
    list_display = ('reference_number', 'book_title', 'author', 'status', 'shelf_location')
    list_filter = ('status', 'acquisition_date')
    search_fields = ('reference_number', 'book__title', 'book__author__name')
    autocomplete_fields = ['book']
    
    fieldsets = (
        ('Book Information', {
            'fields': ('book', 'reference_number')
        }),
        ('Status', {
            'fields': ('status', 'shelf_location')
        }),
        ('Acquisition Details', {
            'fields': ('acquisition_date', 'price')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def book_title(self, obj):
        """Display book title with link to book"""
        url = reverse('admin:library_book_change', args=[obj.book.id])
        return format_html('<a href="{}">{}</a>', url, obj.book.title)
    book_title.short_description = "Title"
    
    def author(self, obj):
        """Display book author"""
        return obj.book.author.name
    author.short_description = "Author"


class ReservationInline(admin.TabularInline):
    """Inline admin for book reservations"""
    model = Reservation
    extra = 0
    fields = ('book', 'reservation_date', 'expiry_date', 'status')
    readonly_fields = ('reservation_date',)
    

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    """Admin configuration for loans"""
    list_display = ('id', 'book_title', 'member_name', 'checkout_date', 
                   'due_date', 'status', 'is_overdue_indicator', 'total_fees')
    list_filter = ('status', 'checkout_date', 'due_date')
    search_fields = ('book_copy__book__title', 'member__user__username', 
                   'member__user__first_name', 'member__user__last_name')
    date_hierarchy = 'checkout_date'
    autocomplete_fields = ['member', 'book_copy']
    inlines = [FeeInline]
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('member', 'book_copy')
        }),
        ('Dates', {
            'fields': ('checkout_date', 'due_date', 'return_date')
        }),
        ('Status', {
            'fields': ('status', 'renewed_count')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def book_title(self, obj):
        """Display book title"""
        return obj.book_copy.book.title
    book_title.short_description = "Book"
    
    def member_name(self, obj):
        """Display member name with link"""
        url = reverse('admin:circulation_member_change', args=[obj.member.id])
        return format_html('<a href="{}">{}</a>', url, obj.member)
    member_name.short_description = "Member"
    
    def is_overdue_indicator(self, obj):
        """Display overdue status with color indicator"""
        if obj.return_date:
            return format_html('<span style="color: green;">Returned</span>')
        elif obj.is_overdue:
            days = (timezone.now().date() - obj.due_date).days
            return format_html('<span style="color: red;">Overdue ({} days)</span>', days)
        else:
            days = (obj.due_date - timezone.now().date()).days
            return format_html('<span style="color: blue;">{} days left</span>', days)
    is_overdue_indicator.short_description = "Status"
    
    def total_fees(self, obj):
        """Display total fees for loan"""
        total = sum(fee.amount for fee in obj.fees.all() if fee.status == 'OU')
        if total > 0:
            return f"${total:.2f}"
        return "$0.00"
    total_fees.short_description = "Fees"
    
    def save_model(self, request, obj, form, change):
        """Custom save logic for loans"""
        creating = not obj.pk
        super().save_model(request, obj, form, change)
        
        # When returning a book via admin, ensure status is updated
        if 'return_date' in form.changed_data and obj.return_date and obj.status != 'RE':
            obj.book_copy.mark_as_available()


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin configuration for reservations"""
    list_display = ('id', 'book_title', 'member_name', 'reservation_date', 
                   'expiry_date', 'status', 'days_left')
    list_filter = ('status', 'reservation_date', 'expiry_date')
    search_fields = ('book__title', 'member__user__username', 'member__user__first_name', 
                     'member__user__last_name')
    date_hierarchy = 'reservation_date'
    autocomplete_fields = ['member', 'book']
    
    actions = ['fulfill_reservations', 'cancel_reservations']
    
    def book_title(self, obj):
        """Display book title with link"""
        url = reverse('admin:library_book_change', args=[obj.book.id])
        return format_html('<a href="{}">{}</a>', url, obj.book.title)
    book_title.short_description = "Book"
    
    def member_name(self, obj):
        """Display member name with link"""
        url = reverse('admin:circulation_member_change', args=[obj.member.id])
        return format_html('<a href="{}">{}</a>', url, obj.member)
    member_name.short_description = "Member"
    
    def days_left(self, obj):
        """Display days left until expiry"""
        if obj.status != 'AC':
            return '-'
        
        days = (obj.expiry_date - timezone.now().date()).days
        if days < 0:
            return format_html('<span style="color: red;">Expired</span>')
        return days
    days_left.short_description = "Days Left"
    
    def fulfill_reservations(self, request, queryset):
        """Action to fulfill selected reservations"""
        fulfilled = 0
        for reservation in queryset.filter(status='AC'):
            # Find available copy
            copies = BookCopy.objects.filter(book=reservation.book, status='AV').first()
            if copies:
                try:
                    reservation.fulfill(copies)
                    fulfilled += 1
                except Exception:
                    pass
        
        self.message_user(request, f"Successfully fulfilled {fulfilled} reservations.")
    fulfill_reservations.short_description = "Fulfill selected reservations"
    
    def cancel_reservations(self, request, queryset):
        """Action to cancel selected reservations"""
        cancelled = queryset.filter(status='AC').update(status='CA')
        self.message_user(request, f"Successfully cancelled {cancelled} reservations.")
    cancel_reservations.short_description = "Cancel selected reservations"


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    """Admin configuration for fees"""
    list_display = ('id', 'loan_details', 'fee_type', 'amount', 'date_assessed', 
                   'status', 'date_paid')
    list_filter = ('fee_type', 'status', 'date_assessed', 'date_paid')
    search_fields = ('loan__book_copy__book__title', 'loan__member__user__username', 
                   'loan__member__user__first_name', 'loan__member__user__last_name')
    date_hierarchy = 'date_assessed'
    
    actions = ['mark_as_paid', 'waive_fees']
    
    def loan_details(self, obj):
        """Display loan details with link"""
        url = reverse('admin:circulation_loan_change', args=[obj.loan.id])
        return format_html('<a href="{}">{}</a>', url, obj.loan)
    loan_details.short_description = "Loan"
    
    def mark_as_paid(self, request, queryset):
        """Action to mark fees as paid"""
        paid = queryset.filter(status='OU').update(
            status='PA', 
            date_paid=timezone.now().date()
        )
        self.message_user(request, f"Successfully marked {paid} fees as paid.")
    mark_as_paid.short_description = "Mark selected fees as paid"
    
    def waive_fees(self, request, queryset):
        """Action to waive fees"""
        waived = queryset.filter(status='OU').update(status='WA')
        self.message_user(request, f"Successfully waived {waived} fees.")
    waive_fees.short_description = "Waive selected fees"