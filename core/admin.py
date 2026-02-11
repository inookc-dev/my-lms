from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Account, Term, User, Video, VideoProgress


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    커스텀 User 모델에 sis_id, avatar_url, time_zone 등을 노출하는 Admin.
    """

    list_display = (
        "id",
        "username",
        "email",
        "sis_id",
        "first_name",
        "last_name",
        "time_zone",
        "is_staff",
        "is_active",
        "last_login",
    )
    search_fields = ("username", "email", "sis_id", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active", "time_zone")

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Canvas 관련 정보",
            {
                "fields": (
                    "sis_id",
                    "avatar_url",
                    "time_zone",
                )
            },
        ),
    )

    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "Canvas 관련 정보",
            {
                "classes": ("wide",),
                "fields": ("sis_id", "avatar_url", "time_zone"),
            },
        ),
    )


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "parent")
    search_fields = ("name",)
    list_filter = ("parent",)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "start_date", "end_date")
    search_fields = ("name",)
    list_filter = ("start_date", "end_date")


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "course", "duration", "video_url", "video_file")
    search_fields = ("title",)
    list_filter = ("course",)


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "video", "watched_time", "is_completed")
    search_fields = ("user__username", "video__title")
    list_filter = ("is_completed",)

