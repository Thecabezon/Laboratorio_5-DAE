from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Shelf, InventoryItem, Acquisition
from .forms import ShelfForm, InventoryItemForm, AcquisitionForm, InventorySearchForm

class ShelfListView(LoginRequiredMixin, ListView):
    model = Shelf
    context_object_name = 'shelves'
    template_name = 'inventory/shelf_list.html'
    paginate_by = 10

class ShelfDetailView(LoginRequiredMixin, DetailView):
    model = Shelf
    context_object_name = 'shelf'
    template_name = 'inventory/shelf_detail.html'

class InventoryItemListView(LoginRequiredMixin, ListView):
    model = InventoryItem
    context_object_name = 'items'
    template_name = 'inventory/inventory_item_list.html'
    paginate_by = 20

    def get_queryset(self):
        queryset = InventoryItem.objects.all()
        form = InventorySearchForm(self.request.GET)
        if form.is_valid():
            if form.cleaned_data['search']:
                queryset = queryset.filter(
                    book__title__icontains=form.cleaned_data['search']
                )
            if form.cleaned_data['condition']:
                queryset = queryset.filter(
                    condition=form.cleaned_data['condition']
                )
            if form.cleaned_data['needs_restock']:
                queryset = queryset.filter(
                    quantity__lte=models.F('minimum_quantity')
                )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = InventorySearchForm(self.request.GET)
        return context

class AcquisitionCreateView(LoginRequiredMixin, CreateView):
    model = Acquisition
    form_class = AcquisitionForm
    template_name = 'inventory/acquisition_form.html'
    success_url = reverse_lazy('inventory:acquisition-list')

    def form_valid(self, form):
        messages.success(self.request, 'Adquisición registrada exitosamente.')
        return super().form_valid(form)