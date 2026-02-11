"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from core.views import (
    LogoutViewAllowGet,
    admin_dashboard,
    course_catalog,
    enroll_course,
    dashboard,
    signup,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("custom-admin/", admin_dashboard, name="admin_dashboard"),
    path("catalog/", course_catalog, name="course_catalog"),
    path("courses/<int:course_id>/enroll/", enroll_course, name="enroll_course"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "accounts/logout/",
        LogoutViewAllowGet.as_view(),
        name="logout",
    ),
    path(
        "accounts/signup/",
        signup,
        name="signup",
    ),
    path("admin/", admin.site.urls),
    path("api/core/", include("core.urls")),
    path("api/courses/", include("courses.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
