from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.views import View
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.db.models import Count, Q, Sum, Case, When, Value, CharField
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required # Ensure this is here
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from django.contrib import messages # Ensure this is here
from datetime import date, timedelta
import json

# --- Third-Party Library Imports ---
import openpyxl # Ensure this is here
from openpyxl.styles import Font, Alignment # Ensure this is here
from weasyprint import HTML, CSS

# --- Local App Imports ---
from .models import Delivery, Baby
from .forms import DeliveryForm, BabyFormSet, DashboardReportFilterForm, NilReportFilterForm # Ensure NilReportFilterForm is defined
from .data import LOCATION_DATA, DISTRICT_CHOICES, FACILITY_TYPES
from accounts.models import Profile # <--- Correct Import for your Profile model
from django.contrib.auth import get_user_model # To get the active User model

User = get_user_model() # Define User here for consistency

# ==========================================================
# HELPER FUNCTIONS & PERMISSION MIXINS
# ==========================================================
def can_modify_data(user):
    """Permission check for users who can create/edit/delete data."""
    return user.is_authenticated and not user.groups.filter(name='ProvinceUser').exists()

class DataEditorRequiredMixin(UserPassesTestMixin):
    """Mixin to apply the can_modify_data permission check to views."""
    def test_func(self):
        return can_modify_data(self.request.user)

# ==========================================================
# DASHBOARD VIEW
# ==========================================================
from django.views.generic import TemplateView
from django.db.models import Count, Q, Sum
from datetime import date, timedelta
import json

class LandingPageView(TemplateView):
    template_name = 'landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ==================================================
        # FILTER INPUTS
        # ==================================================
        request = self.request
        selected_date = request.GET.get('report_date')
        selected_district = request.GET.get('district')
        selected_municipality = request.GET.get('local_municipality')
        selected_facility = request.GET.get('facility')

        # ==================================================
        # BASE QUERYSETS (SINGLE SOURCE OF TRUTH)
        # ==================================================
        deliveries_qs = Delivery.objects.all()

        babies_qs = Baby.objects.filter(
            is_deleted=False,
            delivery__no_births_to_report=False
        )

        # ==================================================
        # APPLY FILTERS (ON DELIVERIES)
        # ==================================================
        if selected_date:
            deliveries_qs = deliveries_qs.filter(report_date=selected_date)

        if selected_district:
            deliveries_qs = deliveries_qs.filter(district=selected_district)

        if selected_municipality:
            deliveries_qs = deliveries_qs.filter(local_municipality=selected_municipality)

        if selected_facility:
            deliveries_qs = deliveries_qs.filter(facility=selected_facility)

        # ==================================================
        # SYNC BABIES WITH FILTERED DELIVERIES
        # ==================================================
        babies_qs = babies_qs.filter(delivery__in=deliveries_qs)

        # ==================================================
        # KPI CARDS
        # ==================================================
        context['total_births'] = babies_qs.count()
        context['total_males'] = babies_qs.filter(gender='Male').count()
        context['total_females'] = babies_qs.filter(gender='Female').count()
        context['total_nil_reports'] = deliveries_qs.filter(
            no_births_to_report=True
        ).count()

        # ==================================================
        # SUMMARY GROUPING LOGIC
        # ==================================================
        if selected_facility:
            group_by = 'facility'
            header = 'Facility'
            footer = selected_facility
            title = f'Births in {selected_facility}'

        elif selected_municipality:
            group_by = 'facility'
            header = 'Facility'
            footer = selected_municipality
            title = f'Births per Facility in {selected_municipality}'

        elif selected_district:
            group_by = 'local_municipality'
            header = 'Local Municipality'
            footer = selected_district
            title = f'Births per Local Municipality in {selected_district}'

        else:
            group_by = 'district'
            header = 'District'
            footer = 'Eastern Cape'
            title = 'Births per District'

        # ==================================================
        # SUMMARY TABLE (SOFT DELETE SAFE)
        # ==================================================
        summary_data = deliveries_qs.filter(
            no_births_to_report=False
        ).values(group_by).annotate(
            total_babies=Count(
                'babies',
                filter=Q(babies__is_deleted=False),
                distinct=True
            ),
            male_count=Count(
                'babies',
                filter=Q(babies__gender='Male', babies__is_deleted=False),
                distinct=True
            ),
            female_count=Count(
                'babies',
                filter=Q(babies__gender='Female', babies__is_deleted=False),
                distinct=True
            ),
        ).order_by(group_by)

        # ==================================================
        # CONTEXT PAYLOAD
        # ==================================================
        context.update({
            # Summary
            'summary_title': title,
            'summary_table_header': header,
            'summary_footer_title': footer,
            'summary_group_by': group_by,
            'summary_data': summary_data,

            # Filters
            'district_list': [d[0] for d in DISTRICT_CHOICES if d[0]],
            'selected_date': selected_date,
            'selected_district': selected_district,
            'selected_municipality': selected_municipality,
            'selected_facility': selected_facility,
        })

        return context

# ==========================================================
# NEW REPORTING VIEW: EXPORT USER LIST
# ==========================================================
@login_required
def export_user_list_excel(request):
    user = request.user

    if not user.is_superuser:
        messages.error(request, "You do not have permission to export the user list.")
        return redirect('landing_page') 

    queryset = User.objects.select_related('profile').order_by('first_name', 'last_name')

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'User List Report'

    headers = [
        'Name', 'Surname', 'Email', 'Title', 'Designation',
        'Persal Number', 'Mobile Number', 'Role(s)',
        'Allocated District', 'Allocated Local Municipality', 'Allocated Facility',
        'Active Account', 'Superuser Status'
    ]
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = openpyxl.styles.PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    for col_num, title in enumerate(headers, 1):
        cell = sheet.cell(row=1, column=col_num, value=title)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    for app_user in queryset:
        user_profile = None
        try:
            user_profile = app_user.profile 
        except Profile.DoesNotExist:
            pass

        roles_str = ", ".join([group.name for group in app_user.groups.all()])

        row_data = [
            app_user.first_name,
            app_user.last_name,
            app_user.email,
            user_profile.title if user_profile else '',
            user_profile.designation if user_profile else '',
            user_profile.persal_number if user_profile else '',
            user_profile.mobile_number if user_profile else '',
            roles_str,
            user_profile.district if user_profile else '',
            user_profile.local_municipality if user_profile else '',
            user_profile.facility if user_profile else '',
            'Yes' if app_user.is_active else 'No', 
            'Yes' if app_user.is_superuser else 'No',
        ]
        sheet.append(row_data)

    for col in sheet.columns:
        length = max(len(str(cell.value or '')) for cell in col)
        sheet.column_dimensions[col[0].column_letter].width = length + 2
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="user_list_report.xlsx"'
    workbook.save(response)
    return response

# ==========================================================
# AJAX HELPER VIEWS
# ==========================================================
def load_options(request):
    parent_type = request.GET.get('type')
    parent_id = request.GET.get('id')
    
    options_list = []
    if parent_type == 'district' and parent_id:
        options_list = LOCATION_DATA['municipalities'].get(parent_id, [])
    elif parent_type == 'municipality' and parent_id:
        options_list = LOCATION_DATA['facilities'].get(parent_id, [])
        
    return JsonResponse({'options': options_list})

def get_facility_type(request):
    facility_name = request.GET.get('facility_name')
    if not facility_name:
        return JsonResponse({'error': 'No facility name provided'}, status=400)

    facility_type = FACILITY_TYPES.get(facility_name)
    
    if facility_type is None:
        return JsonResponse({'error': 'Facility type not found'}, status=404)
        
    return JsonResponse({'facility_type': facility_type})

