# births/views.py

# --- Django Core Imports ---
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Count, Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from datetime import date
import json

# --- Third-Party Library Imports ---
import openpyxl
from openpyxl.styles import Font, Alignment
from weasyprint import HTML, CSS

# --- Local App Imports ---
from .models import Delivery, Baby
from .forms import DeliveryForm, BabyFormSet, DashboardReportFilterForm
from .data import LOCATION_DATA, DISTRICT_CHOICES

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def is_admin_or_superuser(user):
    """Permission check for admin-level reporting views."""
    return user.is_superuser or user.groups.filter(name='Admin').exists()


# ==========================================================
# PUBLIC DASHBOARD VIEW
# ==========================================================
class LandingPageView(TemplateView):
    template_name = 'landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 1. Get and clean filter values from the URL
        selected_date = self.request.GET.get('report_date') or None
        selected_district = self.request.GET.get('district') or None
        selected_municipality = self.request.GET.get('local_municipality') or None
        selected_facility = self.request.GET.get('facility') or None

        # 2. Filter the base queryset for deliveries
        deliveries_qs = Delivery.objects.all()
        if selected_date: deliveries_qs = deliveries_qs.filter(report_date=selected_date)
        if selected_district: deliveries_qs = deliveries_qs.filter(district=selected_district)
        if selected_municipality: deliveries_qs = deliveries_qs.filter(local_municipality=selected_municipality)
        if selected_facility: deliveries_qs = deliveries_qs.filter(facility=selected_facility)
        
        # 3. Create the babies queryset based on the filtered deliveries
        babies_qs = Baby.objects.filter(delivery__in=deliveries_qs)

        # 4. KPI Card Calculations
        total_births = babies_qs.count()
        total_males = babies_qs.filter(gender='Male').count()
        total_females = babies_qs.filter(gender='Female').count()
        total_nil_reports = deliveries_qs.filter(no_births_to_report=True).count()

        # 5. Dynamic Summary Table Logic
        if selected_facility:
            group_by, title, header, footer = 'facility', f'Births in {selected_facility}', 'Facility', selected_facility
        elif selected_municipality:
            group_by, title, header, footer = 'facility', f'Births per Facility in {selected_municipality}', 'Facility', selected_municipality
        elif selected_district:
            group_by, title, header, footer = 'local_municipality', f'Births per Local Municipality in {selected_district}', 'Local Municipality', selected_district
        else:
            group_by, title, header, footer = 'district', 'Births per District', 'District', 'Eastern Cape'
        
        summary_data = deliveries_qs.filter(no_births_to_report=False).values(group_by).annotate(
            total_babies=Count('babies'), male_count=Count('babies', filter=Q(babies__gender='Male')),
            female_count=Count('babies', filter=Q(babies__gender='Female'))).order_by(group_by)
        
        context.update({'summary_title': title, 'summary_table_header': header, 'summary_footer_title': footer, 'summary_group_by': group_by})

        # 6. Other Chart/Table Data Queries
        
        # Age Group Calculation
        age_group_labels = ["10-14 yrs", "15-19 yrs", "20-35 yrs", "35+ yrs"]
        age_group_summary = {label: {'male_count': 0, 'female_count': 0, 'total': 0} for label in age_group_labels}
        today = date.today()
        deliveries_with_dob = deliveries_qs.filter(mother_dob__isnull=False, no_births_to_report=False).prefetch_related('babies')
        for delivery in deliveries_with_dob:
            age = today.year - delivery.mother_dob.year - ((today.month, today.day) < (delivery.mother_dob.month, delivery.mother_dob.day))
            age_group = None
            if 10 <= age <= 14: age_group = "10-14 yrs"
            elif 15 <= age <= 19: age_group = "15-19 yrs"
            elif 20 <= age <= 35: age_group = "20-35 yrs"
            elif age > 35: age_group = "35+ yrs"
            if age_group:
                for baby in delivery.babies.all():
                    if baby.gender == 'Male': age_group_summary[age_group]['male_count'] += 1
                    elif baby.gender == 'Female': age_group_summary[age_group]['female_count'] += 1
                    age_group_summary[age_group]['total'] += 1
        
        # --- CORRECTED BIRTH MODE QUERY ---
        birth_mode_summary = deliveries_qs.filter(
            no_births_to_report=False, birth_mode__isnull=False
        ).exclude(
            birth_mode__exact=''
        ).values('birth_mode').annotate(
            male_count=Count('babies', filter=Q(babies__gender='Male')),
            female_count=Count('babies', filter=Q(babies__gender='Female')),
            total=Count('babies') # This now correctly counts babies for each mode
        ).order_by('birth_mode')

        time_slot_summary = deliveries_qs.filter(no_births_to_report=False).values('time_slot').annotate(male_count=Count('babies', filter=Q(babies__gender='Male')), female_count=Count('babies', filter=Q(babies__gender='Female')), total_in_slot=Count('babies')).order_by('time_slot')
        facility_type_summary = deliveries_qs.filter(no_births_to_report=False).values('facility_type').annotate(male_count=Count('babies', filter=Q(babies__gender='Male')), female_count=Count('babies', filter=Q(babies__gender='Female')), total_in_type=Count('babies')).order_by('facility_type')

        # 7. Pass all data to the context
        context.update({
            'total_births': total_births, 'total_males': total_males, 'total_females': total_females,
            'total_nil_reports': total_nil_reports, 'summary_data': summary_data,
            'form_title': "Festive Season Dashboard", 'selected_date': selected_date, 'selected_district': selected_district,
            'selected_municipality': selected_municipality, 'selected_facility': selected_facility,
            'district_list': [d[0] for d in DISTRICT_CHOICES if d[0]],

            # Data for tables
            'age_group_summary': age_group_summary,
            'birth_mode_summary': birth_mode_summary, # Pass the full summary for the table
            'time_slot_summary': time_slot_summary,
            'facility_type_summary': facility_type_summary,

            # Data for charts on the web dashboard
            'age_group_labels': json.dumps(list(age_group_summary.keys())),
            'age_group_data': json.dumps([d['total'] for d in age_group_summary.values()]),
            'birth_mode_labels': json.dumps([item['birth_mode'] for item in birth_mode_summary]), 
            'birth_mode_data': json.dumps([item['total'] for item in birth_mode_summary]),
        })
        return context

# ==========================================================
# AUTHENTICATED CRUD VIEWS
# ==========================================================
class DeliveryListView(LoginRequiredMixin, ListView):
    model = Delivery; template_name = 'births/birth_list.html'; context_object_name = 'deliveries'; paginate_by = 25
    def get_queryset(self):
        user = self.request.user; queryset = super().get_queryset().prefetch_related('babies').order_by('-timestamp')
        if not user.is_superuser:
            if user.groups.filter(name='Admin').exists(): queryset = queryset.filter(district=user.profile.district)
            elif user.groups.filter(name='User').exists(): queryset = queryset.filter(facility=user.profile.facility)
            else: return queryset.none()
        query = self.request.GET.get('q')
        if query: queryset = queryset.filter(Q(facility__icontains=query) | Q(mother_name__icontains=query) | Q(mother_surname__icontains=query) | Q(birth_mode__icontains=query))
        return queryset

class DeliveryCreateView(LoginRequiredMixin, CreateView):
    model = Delivery; form_class = DeliveryForm; template_name = 'births/birth_form.html'; success_url = reverse_lazy('delivery_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['form_title'], context['submit_button_text'] = 'Add New Delivery Record', 'Submit Record'
        if self.request.POST: context['baby_formset'] = BabyFormSet(self.request.POST, prefix='babies')
        else: context['baby_formset'] = BabyFormSet(prefix='babies')
        return context
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs(); kwargs['user'] = self.request.user; return kwargs
    def form_valid(self, form):
        context = self.get_context_data(); baby_formset = context['baby_formset']
        if form.is_valid() and baby_formset.is_valid():
            with transaction.atomic():
                form.instance.captured_by = self.request.user; self.object = form.save()
                if not form.cleaned_data.get('no_births_to_report'):
                    for baby_form in baby_formset:
                        if baby_form.has_changed(): baby = baby_form.save(commit=False); baby.delivery = self.object; baby.save()
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

class DeliveryUpdateView(LoginRequiredMixin, UpdateView):
    model = Delivery; form_class = DeliveryForm; template_name = 'births/birth_form.html'; success_url = reverse_lazy('delivery_list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['form_title'], context['submit_button_text'] = 'Edit Delivery Record', 'Update Record'
        if self.request.POST: context['baby_formset'] = BabyFormSet(self.request.POST, instance=self.object, prefix='babies')
        else: context['baby_formset'] = BabyFormSet(instance=self.object, prefix='babies')
        return context
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs(); kwargs['user'] = self.request.user; return kwargs
    def post(self, request, *args, **kwargs):
        self.object = self.get_object(); form = self.get_form(); baby_formset = BabyFormSet(request.POST, instance=self.object, prefix='babies')
        if form.is_valid() and baby_formset.is_valid(): return self.form_valid(form, baby_formset)
        else: print(f"--- FORM ERRORS ---\n{form.errors}\n--- FORMSET ERRORS ---\n{baby_formset.errors}\n--------------------"); return self.form_invalid(form, baby_formset)
    def form_valid(self, form, baby_formset):
        with transaction.atomic(): self.object = form.save(); baby_formset.save()
        return redirect(self.get_success_url())
    def form_invalid(self, form, baby_formset):
        return self.render_to_response(self.get_context_data(form=form, baby_formset=baby_formset))

class DeliveryDeleteView(LoginRequiredMixin, DeleteView):
    model = Delivery; template_name = 'births/birth_confirm_delete.html'; success_url = reverse_lazy('delivery_list')

# ==========================================================
# REPORTING VIEWS
# ==========================================================
@login_required
def export_full_report_excel(request):
    user = request.user
    queryset = Delivery.objects.prefetch_related('babies').order_by('timestamp')

    # Apply permission-based filtering
    if not user.is_superuser:
        if user.groups.filter(name='Admin').exists():
            queryset = queryset.filter(district=user.profile.district)
        elif user.groups.filter(name='User').exists():
            queryset = queryset.filter(facility=user.profile.facility)
        else:
            queryset = queryset.none()

    # --- SETUP EXCEL WORKBOOK ---
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Festive Births Full Report'

    # 1. ADD THE NEW 'TIME OF BIRTH' HEADER
    headers = [
        'Timestamp', 'Report Date', 'Time Slot', 'Time of Birth', 'District', 
        'Local Municipality', 'Facility', 'Facility Type', 'Mother Full Name', 
        'Mother D.O.B.', 'Gravidity', 'Parity', 'Birth Mode', 'Born Before Arrival', 
        'Baby Number', 'Baby Gender', 'Baby Weight (grams)'
    ]
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = openpyxl.styles.PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")

    for col_num, title in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_num, value=title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    # --- POPULATE DATA ---
    for delivery in queryset:
        # 2. ADD THE 'delivery_time' FIELD TO THE COMMON DATA LIST
        common_data = [
            delivery.timestamp.strftime('%Y-%m-%d %H:%M'),
            delivery.report_date,
            delivery.time_slot,
            delivery.delivery_time.strftime('%H:%M') if delivery.delivery_time else '', # Format the time
            delivery.district,
            delivery.local_municipality,
            delivery.facility,
            delivery.facility_type,
            delivery.mother_full_name,
            delivery.mother_dob.strftime('%Y-%m-%d') if delivery.mother_dob else '',
            delivery.gravidity,
            delivery.parity,
            delivery.birth_mode,
            'Yes' if delivery.born_before_arrival else 'No',
        ]

        if delivery.no_births_to_report:
            # Add placeholders for baby-specific fields
            sheet.append(common_data + ['NIL Report', 'N/A', 'N/A'])
        else:
            for i, baby in enumerate(delivery.babies.all(), 1):
                # Append baby-specific data to the common data
                sheet.append(common_data + [i, baby.gender, baby.weight])

    # --- FINALIZE AND SERVE ---
    # Auto-size columns
    for col in sheet.columns:
        length = max(len(str(cell.value or '')) for cell in col)
        sheet.column_dimensions[col[0].column_letter].width = length + 2

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="festive_births_full_report.xlsx"'
    workbook.save(response)
    return response

class DashboardReportFilterView(LoginRequiredMixin, TemplateView):
    template_name = 'births/dashboard_report_filter.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs); context['form'] = DashboardReportFilterForm(); context['form_title'] = 'Generate Dashboard PDF Report'; return context

@login_required
def generate_dashboard_pdf(request):
    landing_page_view = LandingPageView(); landing_page_view.request = request; context = landing_page_view.get_context_data()
    report_title = "Provincial Dashboard Report"
    if context.get('selected_facility'): report_title = f"{context['selected_facility']} Report"
    elif context.get('selected_municipality'): report_title = f"{context['selected_municipality']} Report"
    elif context.get('selected_district'): report_title = f"{context['selected_district']} Report"
    context['report_title'] = report_title
    html_string = render_to_string('births/dashboard_pdf.html', context)
    css_path = finders.find('css/pdf_style.css')
    if not css_path: return HttpResponse("Error: CSS file 'pdf_style.css' not found in static directories.", status=500)
    pdf_stylesheet = CSS(filename=css_path)
    weasyprint_html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = weasyprint_html.write_pdf(stylesheets=[pdf_stylesheet, CSS(string='@page { size: A4 landscape; }')])
    response = HttpResponse(pdf_file, content_type='application/pdf'); response['Content-Disposition'] = 'attachment; filename="dashboard_report.pdf"'; return response

# ==========================================================
# AJAX HELPER VIEW
# ==========================================================
def load_options(request):
    parent_type = request.GET.get('type'); parent_id = request.GET.get('id'); options = []
    if parent_type == 'district' and parent_id: options = LOCATION_DATA['municipalities'].get(parent_id, [])
    elif parent_type == 'municipality' and parent_id: options = LOCATION_DATA['facilities'].get(parent_id, [])
    return JsonResponse({'options': options})
