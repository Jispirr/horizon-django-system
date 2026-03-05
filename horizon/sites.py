from django.contrib.admin import AdminSite
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.urls import path


class HorizonAdminSite(AdminSite):
    """Custom admin site that uses Horizon's custom templates and styling."""
    
    site_header = "Horizon Car Dealership"
    site_title = "Horizon Admin"
    index_title = "Dashboard"
    
    def get_urls(self):
        urls = super().get_urls()
        return urls
    
    def index(self, request: HttpRequest, extra_context=None):
        """
        Override the index view to use custom template.
        """
        app_list = self.get_app_list(request)
        
        context = {
            **self.each_context(request),
            'title': self.index_title,
            'app_list': app_list,
            'subtitle': None,
        }
        if extra_context:
            context.update(extra_context)
        
        request.current_app = self.name
        return TemplateResponse(request, 'admin/horizon_admin/index.html', context)


# Create the custom admin site instance
horizon_admin_site = HorizonAdminSite(name='horizon_admin')
