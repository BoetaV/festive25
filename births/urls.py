from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views
from django.contrib.auth.forms import AuthenticationForm

class CustomAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Persal Number"
        self.fields['username'].widget.attrs['placeholder'] = 'Enter your 8-digit Persal Number'

urlpatterns = [
    # --- Public & Auth URLs ---
    path('', views.LandingPageView.as_view(), name='landing_page'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='landing_page'), name='logout'),

    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url = reverse_lazy('password_change_done') # Redirect after success
    ), name='password_change'),
    path(
    'password-change/done/',
    auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
    name='password_change_done'
    ),

    path('reports/dashboard-filter/', views.DashboardReportFilterView.as_view(), name='dashboard_report_filter'),
    path('reports/generate-dashboard-pdf/', views.GenerateDashboardPDF.as_view(), name='generate_dashboard_pdf'),
    
    # List View: The main table of all deliveries
    path('deliveries/', views.DeliveryListView.as_view(), name='delivery_list'),
    
    # Create View: The form to add a new delivery
    path('deliveries/new/', views.DeliveryCreateView.as_view(), name='delivery_create'),
    
    # Update View: The form to edit an existing delivery
    path('deliveries/<int:pk>/edit/', views.DeliveryUpdateView.as_view(), name='delivery_update'),
    
    # Delete View: The confirmation page to delete a delivery
    path('deliveries/<int:pk>/delete/', views.DeliveryDeleteView.as_view(), name='delivery_delete'),

    path('reports/export-excel/', views.export_full_report_excel, name='export_full_report'),
    path('export-users/', views.export_user_list_excel, name='export_user_list_excel'),
    path('reports/abnormal-weights/', views.AbnormalWeightReportView.as_view(), name='report_abnormal_weights'),
    
    # --- AJAX URL for dynamic dropdowns (this remains the same) ---
    path('ajax/get-facility-type/', views.get_facility_type, name='ajax_get_facility_type'),
    path('ajax/load-options/', views.load_options, name='ajax_load_options'),
]
