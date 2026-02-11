from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Canvas 스타일의 사용자 모델.
    - username: Login ID처럼 사용 (기본 Django 필드)
    - email: 시스템 전역에서 유일해야 함
    - sis_id: 선택 입력이지만, 값이 있으면 유일해야 함
    """

    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
        help_text="로그인 및 알림에 사용되는 기본 이메일 (시스템 전역 유일)",
    )
    sis_id = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="SIS 학번/사번. 없을 수도 있지만, 있으면 유일해야 함.",
    )
    avatar_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="사용자 프로필 사진 URL",
    )
    time_zone = models.CharField(
        max_length=50,
        default="UTC",
        help_text="사용자 선호 타임존 (예: UTC, Asia/Seoul)",
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email or self.username


class Role(models.TextChoices):
    """
    Canvas 기본 역할 Enum.
    """

    STUDENT = "student", "Student"
    TEACHER = "teacher", "Teacher"
    TA = "ta", "TA"
    OBSERVER = "observer", "Observer"
    DESIGNER = "designer", "Designer"


class Account(models.Model):
    """
    Canvas의 Account와 유사한 개념.
    - 루트 Account는 parent가 없는 계정
    - 하위 Account는 parent를 통해 상위 계정에 연결
    """

    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        "self",
        related_name="sub_accounts",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text="상위 계정(없으면 루트 계정)",
    )

    class Meta:
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    def __str__(self) -> str:
        if self.parent:
            return f"{self.parent} / {self.name}"
        return self.name


class Term(models.Model):
    """
    수업이 진행되는 기간(학기)을 나타내는 모델.
    Canvas의 Enrollment Term 개념과 유사.
    """

    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ["start_date", "end_date"]
        verbose_name = "Term"
        verbose_name_plural = "Terms"

    def __str__(self) -> str:
        return f"{self.name} ({self.start_date} ~ {self.end_date})"


class Video(models.Model):
    """
    K-LMS 동영상 콘텐츠.
    - video_url: 외부 URL (YouTube, Vimeo, 직접 mp4 링크 등)
    - video_file: 업로드한 동영상 파일 (선택)
    - duration: 총 길이(초)
    """

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="videos",
        help_text="소속 강의",
    )
    title = models.CharField(max_length=255, help_text="동영상 제목")
    video_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="동영상 URL (mp4 직접 링크 등)",
    )
    video_file = models.FileField(
        upload_to="videos/%Y/%m/",
        blank=True,
        null=True,
        help_text="업로드한 동영상 파일",
    )
    duration = models.PositiveIntegerField(
        default=0,
        help_text="총 길이(초)",
    )

    class Meta:
        ordering = ["id"]
        verbose_name = "Video"
        verbose_name_plural = "Videos"

    def __str__(self) -> str:
        return self.title

    def get_src_url(self):
        """템플릿에서 재생에 사용할 URL 반환 (video_url 우선)"""
        if self.video_url:
            return self.video_url
        if self.video_file:
            return self.video_file.url
        return None


class VideoProgress(models.Model):
    """
    학생별 동영상 시청 진도.
    - watched_time: 시청한 시간(초)
    - is_completed: 총 길이의 95% 이상 시청 시 True (출석 완료)
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="video_progresses",
    )
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="progresses",
    )
    watched_time = models.FloatField(default=0, help_text="시청한 시간(초)")
    is_completed = models.BooleanField(default=False, help_text="출석 완료 여부")

    class Meta:
        ordering = ["video", "user"]
        unique_together = [["user", "video"]]
        verbose_name = "Video Progress"
        verbose_name_plural = "Video Progresses"

    def __str__(self) -> str:
        return f"{self.user} - {self.video}: {self.watched_time}s"

