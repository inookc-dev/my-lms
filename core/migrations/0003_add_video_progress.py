# Generated manually for K-LMS Video progress

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0004_submission_feedback"),
        ("core", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Video",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(help_text="동영상 제목", max_length=255)),
                (
                    "video_url",
                    models.URLField(
                        blank=True,
                        help_text="동영상 URL (mp4 직접 링크 등)",
                        max_length=500,
                        null=True,
                    ),
                ),
                (
                    "video_file",
                    models.FileField(
                        blank=True,
                        help_text="업로드한 동영상 파일",
                        null=True,
                        upload_to="videos/%Y/%m/",
                    ),
                ),
                (
                    "duration",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="총 길이(초)",
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        help_text="소속 강의",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="videos",
                        to="courses.course",
                    ),
                ),
            ],
            options={
                "verbose_name": "Video",
                "verbose_name_plural": "Videos",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="VideoProgress",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "watched_time",
                    models.FloatField(
                        default=0,
                        help_text="시청한 시간(초)",
                    ),
                ),
                (
                    "is_completed",
                    models.BooleanField(
                        default=False,
                        help_text="출석 완료 여부",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="video_progresses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "video",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="progresses",
                        to="core.video",
                    ),
                ),
            ],
            options={
                "verbose_name": "Video Progress",
                "verbose_name_plural": "Video Progresses",
                "ordering": ["video", "user"],
                "unique_together": {("user", "video")},
            },
        ),
    ]
