from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator

from .models import Member, BookCopy, Loan, Reservation, Fee


@login_required
@permission_required('circulation.view_member')
def member_list(request):
    """Display list of members"""
    search_query = request.GET.get('search', '')
    member_status = request.GET.get('status', '')
    
    # Base queryset
    members = Member.objects.all()
    
    # Apply filters
    if search_query:
        members = members.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
        
    if member_status == 'active':
        members = members.filter(is_active=True)
    elif member_status == 'inactive':
        members = members.filter(is_active=False)
    
    # Add annotations
    members = members.annotate(
        active_loans=Count('loans', filter=Q(loans__return_date__isnull=True))
    )
    
    # Pagination
    paginator = Paginator(members, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'member_status': member_status,
    }
    
    return render(request, 'circulation/member_list.html', context)


@login_required
@permission_required('circulation.view_loan')
def loan_list(request):
    """Display list of loans"""
    search_query = request.GET.get('search', '')
    loan_status = request.GET.get('status', '')
    
    # Base queryset
    loans = Loan.objects.select_related('member__user', 'book_copy__book')
    
    # Apply filters
    if search_query:
        loans = loans.filter(
            Q(book_copy__book__title__icontains=search_query) |
            Q(book_copy__reference_number__icontains=search_query) |
            Q(member__user__username__icontains=search_query) |
            Q(member__user__first_name__icontains=search_query) |
            Q(member__user__last_name__icontains=search_query)
        )
        
    if loan_status == 'active':
        loans = loans.filter(return_date__isnull=True)
    elif loan_status == 'returned':
        loans = loans.filter(return_date__isnull=False)
    elif loan_status == 'overdue':
        today = timezone.now().date()
        loans = loans.filter(
            return_date__isnull=True,
            due_date__lt=today
        )
    
    # Pagination
    paginator = Paginator(loans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'loan_status': loan_status,
    }
    
    return render(request, 'circulation/loan_list.html', context)


@login_required
@permission_required('circulation.view_loan')
def loan_overdue_list(request):
    """Display list of overdue loans"""
    today = timezone.now().date()
    
    # Get overdue loans
    overdue_loans = Loan.objects.filter(
        return_date__isnull=True,
        due_date__lt=today
    ).select_related('member__user', 'book_copy__book').order_by('due_date')
    
    # Pagination
    paginator = Paginator(overdue_loans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'today': today,
    }
    
    return render(request, 'circulation/overdue_loan_list.html', context)


@login_required
@permission_required('circulation.view_reservation')
def reservation_list(request):
    """Display list of reservations"""
    search_query = request.GET.get('search', '')
    reservation_status = request.GET.get('status', '')
    
    # Base queryset
    reservations = Reservation.objects.select_related('member__user', 'book')
    
    # Apply filters
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        if not member_id:
            messages.error(request, "Member is required to make a reservation.")
            return redirect('circulation:reserve_book', book_id=book.id)
        
        try:
            member = Member.objects.get(id=member_id)
            
            # Optional: Check if member already has a reservation for this book
            existing_reservation = Reservation.objects.filter(member=member, book=book, status='AC').exists()
            if existing_reservation:
                messages.warning(request, "You already have an active reservation for this book.")
                return redirect('circulation:book_detail', book_id=book.id)

            # Create reservation
            Reservation.objects.create(
                member=member,
                book=book,
                status='AC',
                reserved_date=timezone.now().date()
            )
            messages.success(request, f"Book '{book.title}' reserved successfully.")
            return redirect('circulation:reservation_list')
        
        except Member.DoesNotExist:
            messages.error(request, "Selected member does not exist.")
            return redirect('circulation:reserve_book', book_id=book.id)

    context = {
        'book': book,
        'members': Member.objects.filter(is_active=True)
    }

    return render(request, 'circulation/reserve_form.html', context)

@login_required
@permission_required('circulation.view_reservation')
def reservation_list(request):
    """Display list of reservations"""
    search_query = request.GET.get('search', '')
    reservation_status = request.GET.get('status', '')
    
    # Base queryset
    reservations = Reservation.objects.select_related('member__user', 'book')
    
    # Apply filters
    if search_query:
        reservations = reservations.filter(
            Q(book__title__icontains=search_query) |
            Q(member__user__username__icontains=search_query) |
            Q(member__user__first_name__icontains=search_query) |
            Q(member__user__last_name__icontains=search_query)
        )
        
    if reservation_status == 'active':
        reservations = reservations.filter(status='AC')
    elif reservation_status == 'fulfilled':
        reservations = reservations.filter(status='FU')
    elif reservation_status == 'cancelled':
        reservations = reservations.filter(status='CA')
    elif reservation_status == 'expired':
        reservations = reservations.filter(status='EX')
    
    # Pagination
    paginator = Paginator(reservations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'reservation_status': reservation_status,
    }
    
    return render(request, 'circulation/reservation_list.html', context)


@login_required
@permission_required('circulation.add_loan')
def checkout_book(request, copy_id=None):
    """Check out a book to a member"""
    # This is a placeholder for the checkout functionality
    # In a real implementation, this would include a form to select a member
    # and process the checkout
    
    if request.method == 'POST':
        # Process form submission
        member_id = request.POST.get('member_id')
        book_copy_id = request.POST.get('book_copy_id') or copy_id
        due_date = request.POST.get('due_date')
        
        if not all([member_id, book_copy_id, due_date]):
            messages.error(request, "All fields are required")
            return redirect('circulation:checkout_book')
        
        try:
            member = Member.objects.get(id=member_id)
            book_copy = BookCopy.objects.get(id=book_copy_id)
            due_date = timezone.datetime.strptime(due_date, '%Y-%m-%d').date()
            
            # Check if member can borrow
            if not member.can_borrow():
                messages.error(request, f"{member} has reached borrowing limit or has an invalid membership")
                return redirect('circulation:checkout_book')
            
            # Check if book is available
            if not book_copy.is_available:
                messages.error(request, f"Book copy {book_copy.reference_number} is not available")
                return redirect('circulation:checkout_book')
            
            # Create loan
            loan = Loan.objects.create(
                member=member,
                book_copy=book_copy,
                checkout_date=timezone.now().date(),
                due_date=due_date
            )
            
            messages.success(request, f"Successfully checked out {book_copy.book.title} to {member}")
            return redirect('circulation:loan_detail', loan_id=loan.id)
            
        except (Member.DoesNotExist, BookCopy.DoesNotExist, ValueError) as e:
            messages.error(request, f"Error processing checkout: {str(e)}")
            return redirect('circulation:checkout_book')
    
    # Display checkout form
    context = {
        'members': Member.objects.filter(is_active=True),
        'book_copy': BookCopy.objects.get(id=copy_id) if copy_id else None,
        'default_due_date': (timezone.now() + timezone.timedelta(weeks=2)).date()
    }
    
    return render(request, 'circulation/checkout_form.html', context)


@login_required
@permission_required('circulation.change_loan')
def return_book(request, loan_id):
    """Process book return"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    # Check if book is already returned
    if loan.return_date:
        messages.warning(request, f"This book was already returned on {loan.return_date}")
        return redirect('circulation:loan_detail', loan_id=loan.id)
    
    if request.method == 'POST':
        status = request.POST.get('status', 'RE')  # Default to returned
        
        damaged = status == 'DA'
        lost = status == 'LO'
        
        # Process return
        loan.return_book(damaged=damaged, lost=lost)
        
        messages.success(request, f"Successfully processed return of {loan.book_copy.book.title}")
        return redirect('circulation:loan_detail', loan_id=loan.id)
    
    context = {
        'loan': loan
    }
    
    return render(request, 'circulation/return_form.html', context)


@login_required
@permission_required('circulation.change_loan')
def renew_loan(request, loan_id):
    """Renew a loan"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    # Check if loan can be renewed
    if loan.return_date:
        messages.error(request, "Cannot renew a returned loan")
        return redirect('circulation:loan_detail', loan_id=loan.id)
    
    if loan.renewed_count >= 3:
        messages.error(request, "This loan has already been renewed the maximum number of times")
        return redirect('circulation:loan_detail', loan_id=loan.id)
    
    if request.method == 'POST':
        try:
            weeks = int(request.POST.get('weeks', 2))
            loan.renew(weeks=weeks)
            messages.success(request, f"Successfully renewed loan until {loan.due_date}")
        except ValueError as e:
            messages.error(request, f"Error renewing loan: {str(e)}")
            
        return redirect('circulation:loan_detail', loan_id=loan.id)
    
    context = {
        'loan': loan,
        'new_due_date': (timezone.now().date() + timezone.timedelta(weeks=2))
    }
    
    return render(request, 'circulation/renew_form.html', context)


@login_required
@permission_required('circulation.view_loan')
def loan_detail(request, loan_id):
    """Display details of a specific loan"""
    loan = get_object_or_404(
        Loan.objects.select_related('member__user', 'book_copy__book'), 
        id=loan_id
    )
    
    context = {
        'loan': loan,
        'fees': loan.fees.all(),
        'is_overdue': loan.is_overdue,
        'today': timezone.now().date(),
    }
    
    return render(request, 'circulation/loan_detail.html', context)


@login_required
@permission_required('circulation.add_reservation')
def reserve_book(request, book_id):
    """Reserve a book"""
    from library.models import Book
    book = get_object_or_404(Book, id=book_id)
    
    # Check if any copies are available
    available_copies = BookCopy.objects.filter(book=book, status='AV').exists()
    
    if available_copies:
        messages.info(request, "This book has available copies. You can check it out instead of reserving.")
    
    if request.method == 'POST':
        member_id = request.POST.get('member_id')
        
        try:
            member = Member.objects.get(id=member_id)
            
            # Check for existing reservation
            existing = Reservation.objects.filter(
                member=member,
                book=book,
                status='AC'
            ).exists()
            
            if existing:
                messages.error(request, f"{member} already has an active reservation for this book")
                return redirect('circulation:reserve_book', book_id=book_id)
            
            # Create reservation
            expiry_date = timezone.now().date() + timezone.timedelta(weeks=1)
            
            reservation = Reservation.objects.create(
                member=member,
                book=book,
                expiry_date=expiry_date
            )
            
            messages.success(request, f"Successfully reserved {book.title} for {member}")
            return redirect('circulation:reservation_detail', reservation_id=reservation.id)
            
        except Member.DoesNotExist:
            messages.error(request, "Invalid member selected")
            return redirect('circulation:reserve_book', book_id=book_id)
    
    context = {
        'book': book,
        'members': Member.objects.filter(is_active=True),
        'available_copies': available_copies,
    }
    
    return render(request, 'circulation/reserve_form.html', context)


@login_required
@permission_required('circulation.view_reservation')
def reservation_detail(request, reservation_id):
    """Display details of a specific reservation"""
    reservation = get_object_or_404(
        Reservation.objects.select_related('member__user', 'book'), 
        id=reservation_id
    )
    
    # Check for available copies
    available_copies = BookCopy.objects.filter(book=reservation.book, status='AV')
    
    context = {
        'reservation': reservation,
        'available_copies': available_copies,
        'today': timezone.now().date(),
    }
    
    return render(request, 'circulation/reservation_detail.html', context)


@login_required
@permission_required('circulation.add_fee', 'circulation.change_fee')
def manage_fees(request, loan_id):
    """Manage fees for a loan"""
    loan = get_object_or_404(Loan, id=loan_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        fee_id = request.POST.get('fee_id')
        
        if action == 'add':
            # Add new fee
            try:
                fee_type = request.POST.get('fee_type')
                amount = float(request.POST.get('amount'))
                description = request.POST.get('description', '')
                
                Fee.objects.create(
                    loan=loan,
                    fee_type=fee_type,
                    amount=amount,
                    description=description
                )
                
                messages.success(request, f"Successfully added {fee_type} fee of ${amount:.2f}")
                
            except ValueError:
                messages.error(request, "Invalid amount entered for fee")
                
        elif action == 'pay' and fee_id:
            # Mark fee as paid
            try:
                fee = Fee.objects.get(id=fee_id, loan=loan)
                fee.mark_as_paid()
                messages.success(request, f"Marked fee of ${fee.amount:.2f} as paid")
                
            except Fee.DoesNotExist:
                messages.error(request, "Fee not found")
                
        elif action == 'waive' and fee_id:
            # Waive fee
            try:
                fee = Fee.objects.get(id=fee_id, loan=loan)
                fee.waive()
                messages.success(request, f"Waived fee of ${fee.amount:.2f}")
                
            except Fee.DoesNotExist:
                messages.error(request, "Fee not found")
        
        return redirect('circulation:manage_fees', loan_id=loan.id)
    
    context = {
        'loan': loan,
        'fees': loan.fees.all(),
        'fee_types': Fee.FEE_TYPE_CHOICES,
    }
    
    return render(request, 'circulation/manage_fees.html', context)


@login_required
@permission_required('circulation.view_member')
def member_report(request):
    """Generate report on members"""
    # Get statistics on members
    total_members = Member.objects.count()
    active_members = Member.objects.filter(is_active=True).count()
    
    # Members by type
    members_by_type = Member.objects.values('membership_type') \
                            .annotate(count=Count('id')) \
                            .order_by('membership_type')
    
    # Top borrowers
    top_borrowers = Member.objects.annotate(
        loan_count=Count('loans')
    ).order_by('-loan_count')[:10]
    
    context = {
        'total_members': total_members,
        'active_members': active_members,
        'members_by_type': members_by_type,
        'top_borrowers': top_borrowers,
    }
    
    return render(request, 'circulation/member_report.html', context)


@login_required
@permission_required('circulation.view_loan')
def circulation_report(request):
    """Generate circulation report"""
    # Get date range for filtering
    from_date_str = request.GET.get('from_date')
    to_date_str = request.GET.get('to_date')
    
    # Default to last 30 days if no dates provided
    today = timezone.now().date()
    from_date = None
    to_date = None
    
    if from_date_str:
        try:
            from_date = timezone.datetime.strptime(from_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    if to_date_str:
        try:
            to_date = timezone.datetime.strptime(to_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if not from_date:
        from_date = today - timezone.timedelta(days=30)
        
    if not to_date:
        to_date = today
    
    # Loans in date range
    loans = Loan.objects.filter(checkout_date__gte=from_date, checkout_date__lte=to_date)
    total_loans = loans.count()
    
    # Returned loans
    returned_loans = loans.filter(return_date__isnull=False).count()
    
    # Overdue loans
    overdue_loans = loans.filter(
        return_date__isnull=True,
        due_date__lt=today
    ).count()
    
    # Most borrowed categories
    from django.db.models import Count
    from library.models import Category
    
    most_borrowed_categories = Category.objects.filter(
        books__copies__loans__checkout_date__gte=from_date,
        books__copies__loans__checkout_date__lte=to_date
    ).annotate(
        loan_count=Count('books__copies__loans')
    ).order_by('-loan_count')[:5]
    
    # Fee collection
    total_fees = Fee.objects.filter(
        loan__checkout_date__gte=from_date,
        loan__checkout_date__lte=to_date
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    collected_fees = Fee.objects.filter(
        loan__checkout_date__gte=from_date,
        loan__checkout_date__lte=to_date,
        status='PA'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'from_date': from_date,
        'to_date': to_date,
        'total_loans': total_loans,
        'returned_loans': returned_loans,
        'overdue_loans': overdue_loans,
        'most_borrowed_categories': most_borrowed_categories,
        'total_fees': total_fees,
        'collected_fees': collected_fees,
    }
    
    return render(request, 'circulation/circulation_report.html', context)