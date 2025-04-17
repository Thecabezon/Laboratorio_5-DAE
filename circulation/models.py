from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from library.models import Book


class Member(models.Model):
    """Library member who can borrow books"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member')
    address = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    membership_date = models.DateField(default=timezone.now)
    membership_expiry = models.DateField(null=True, blank=True)
    
    MEMBERSHIP_TYPES = (
        ('STD', 'Standard'),
        ('PRE', 'Premium'),
        ('STU', 'Student'),
        ('SEN', 'Senior'),
    )
    membership_type = models.CharField(
        max_length=3,
        choices=MEMBERSHIP_TYPES,
        default='STD'
    )
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def is_membership_valid(self):
        if not self.membership_expiry:
            return True
        return self.membership_expiry >= timezone.now().date()
    
    @property
    def active_loans_count(self):
        return self.loans.filter(return_date__isnull=True).count()
    
    def can_borrow(self):
        """Check if member can borrow more books"""
        if not self.is_active:
            return False
        
        if not self.is_membership_valid:
            return False
        
        # Check borrowing limits based on membership type
        limit = {
            'STD': 3,
            'PRE': 5,
            'STU': 2,
            'SEN': 4,
        }.get(self.membership_type, 3)
        
        return self.active_loans_count < limit


class BookCopy(models.Model):
    """Physical copy of a book that can be borrowed"""
    book = models.ForeignKey('library.Book', on_delete=models.CASCADE, related_name='copies')
    reference_number = models.CharField(max_length=50, unique=True)
    acquisition_date = models.DateField(default=timezone.now)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    STATUS_CHOICES = (
        ('AV', 'Available'),
        ('LO', 'On Loan'),
        ('RE', 'Reserved'),
        ('MA', 'Maintenance'),
        ('LO', 'Lost'),
        ('DA', 'Damaged'),
        ('WD', 'Withdrawn'),
    )
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='AV')
    shelf_location = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Book copies"
    
    def __str__(self):
        return f"{self.book.title} ({self.reference_number})"
    
    @property
    def is_available(self):
        return self.status == 'AV'
    
    def mark_as_loaned(self):
        self.status = 'LO'
        self.save()
    
    def mark_as_available(self):
        self.status = 'AV'
        self.save()
    
    def mark_as_reserved(self):
        self.status = 'RE'
        self.save()


class Loan(models.Model):
    """Record of a book being borrowed"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='loans')
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='loans')
    checkout_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    return_date = models.DateField(null=True, blank=True)
    
    LOAN_STATUS_CHOICES = (
        ('AC', 'Active'),
        ('OV', 'Overdue'),
        ('RE', 'Returned'),
        ('LO', 'Lost'),
        ('DA', 'Damaged'),
    )
    status = models.CharField(max_length=2, choices=LOAN_STATUS_CHOICES, default='AC')
    
    renewed_count = models.PositiveSmallIntegerField(default=0)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-checkout_date']
    
    def __str__(self):
        return f"{self.book_copy.book.title} - {self.member}"
    
    def clean(self):
        """Validate loan data"""
        # Cannot borrow if member can't borrow more books
        if not self.member.can_borrow() and not self.pk:
            raise ValidationError("Member has reached borrowing limit or membership is not valid")
        
        # Cannot borrow if book is not available
        if not self.book_copy.is_available and not self.pk:
            raise ValidationError("This book copy is not available for loan")
            
        # Due date must be in the future
        if self.due_date < timezone.now().date():
            raise ValidationError("Due date must be in the future")
    
    def save(self, *args, **kwargs):
        # For new loans, mark the book copy as loaned
        if not self.pk:
            self.book_copy.mark_as_loaned()
            
        # If return date was set, mark the book as available
        if self.return_date and self.status != 'RE':
            self.status = 'RE'
            self.book_copy.mark_as_available()
            
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        if self.return_date:
            return False
        return timezone.now().date() > self.due_date
    
    def renew(self, weeks=2):
        """Renew a loan for a number of weeks"""
        if self.renewed_count >= 3:
            raise ValidationError("Cannot renew more than 3 times")
            
        if self.return_date:
            raise ValidationError("Cannot renew a returned loan")
            
        self.due_date = timezone.now().date() + timezone.timedelta(weeks=weeks)
        self.renewed_count += 1
        self.save()
    
    def return_book(self, damaged=False, lost=False):
        """Process a book return"""
        today = timezone.now().date()
        self.return_date = today
        
        if damaged:
            self.status = 'DA'
            self.book_copy.status = 'DA'
        elif lost:
            self.status = 'LO'
            self.book_copy.status = 'LO'
        else:
            self.status = 'RE'
            self.book_copy.mark_as_available()
            
        self.book_copy.save()
        self.save()
        
        # Calculate late fee if applicable
        if today > self.due_date:
            days_late = (today - self.due_date).days
            fee_amount = days_late * 0.50  # $0.50 per day
            
            # Create late fee record
            Fee.objects.create(
                loan=self,
                fee_type='LA',
                amount=fee_amount,
                description=f"Late fee for {days_late} days"
            )
            
        return True


class Reservation(models.Model):
    """Request to borrow a book that is currently unavailable"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='reservations')
    book = models.ForeignKey('library.Book', on_delete=models.CASCADE, related_name='reservations')
    reservation_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField()
    
    STATUS_CHOICES = (
        ('AC', 'Active'),
        ('FU', 'Fulfilled'),
        ('CA', 'Cancelled'),
        ('EX', 'Expired'),
    )
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='AC')
    
    class Meta:
        ordering = ['reservation_date']
    
    def __str__(self):
        return f"{self.book.title} reserved by {self.member}"
    
    def clean(self):
        """Validate reservation data"""
        # Expiry date must be in the future
        if self.expiry_date <= timezone.now().date():
            raise ValidationError("Expiry date must be in the future")
            
        # Check if member already has an active reservation for this book
        existing = Reservation.objects.filter(
            member=self.member,
            book=self.book,
            status='AC'
        ).exclude(pk=self.pk).exists()
        
        if existing:
            raise ValidationError("Member already has an active reservation for this book")
    
    def save(self, *args, **kwargs):
        # If no expiry date is set, default to 1 week
        if not self.expiry_date:
            self.expiry_date = timezone.now().date() + timezone.timedelta(weeks=1)
            
        super().save(*args, **kwargs)
    
    def fulfill(self, book_copy, checkout_date=None, due_date=None):
        """Create a loan when reservation is fulfilled"""
        if self.status != 'AC':
            raise ValidationError("Cannot fulfill a non-active reservation")
            
        if not book_copy.is_available:
            raise ValidationError("Selected book copy is not available")
        
        # Create loan
        checkout = checkout_date or timezone.now().date()
        due = due_date or (checkout + timezone.timedelta(weeks=2))
        
        loan = Loan.objects.create(
            member=self.member,
            book_copy=book_copy,
            checkout_date=checkout,
            due_date=due
        )
        
        # Update reservation status
        self.status = 'FU'
        self.save()
        
        return loan
    
    def cancel(self):
        """Cancel reservation"""
        if self.status != 'AC':
            raise ValidationError("Cannot cancel a non-active reservation")
            
        self.status = 'CA'
        self.save()
        return True


class Fee(models.Model):
    """Fees associated with loans"""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='fees')
    
    FEE_TYPE_CHOICES = (
        ('LA', 'Late Return'),
        ('DA', 'Damage'),
        ('LO', 'Lost Item'),
        ('PR', 'Processing'),
        ('OT', 'Other'),
    )
    fee_type = models.CharField(max_length=2, choices=FEE_TYPE_CHOICES, default='LA')
    
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date_assessed = models.DateField(default=timezone.now)
    date_paid = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    
    PAYMENT_STATUS_CHOICES = (
        ('OU', 'Outstanding'),
        ('PA', 'Paid'),
        ('WA', 'Waived'),
    )
    status = models.CharField(max_length=2, choices=PAYMENT_STATUS_CHOICES, default='OU')
    
    def __str__(self):
        return f"{self.get_fee_type_display()} fee of ${self.amount:.2f} for {self.loan}"
    
    def mark_as_paid(self, payment_date=None):
        """Mark fee as paid"""
        self.status = 'PA'
        self.date_paid = payment_date or timezone.now().date()
        self.save()
        return True
    
    def waive(self):
        """Waive fee"""
        self.status = 'WA'
        self.save()
        return True