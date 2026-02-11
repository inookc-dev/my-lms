from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet,
    TermViewSet,
    UserViewSet,
    course_detail,
    module_item_detail,
    update_progress,
    video_detail,
    video_list,
)

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"accounts", AccountViewSet)
router.register(r"terms", TermViewSet)

urlpatterns = [
    # HTML course detail & module item detail (currently under /api/core/...)
    path("<int:course_id>/", course_detail, name="course_detail"),
    path(
        "courses/<int:course_id>/items/<int:item_id>/",
        module_item_detail,
        name="module_item_detail",
    ),
    # Video progress (K-LMS)
    path(
        "courses/<int:course_id>/videos/",
        video_list,
        name="video_list",
    ),
    path(
        "videos/<int:video_id>/",
        video_detail,
        name="video_detail",
    ),
    path(
        "videos/update-progress/",
        update_progress,
        name="update_progress",
    ),
]

urlpatterns += router.urls

