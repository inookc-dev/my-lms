from django.contrib import admin

from .models import (
    Assignment,
    Choice,
    Course,
    Enrollment,
    Module,
    ModuleItem,
    Page,
    Question,
    Quiz,
    QuizAttempt,
    Section,
    StudentAnswer,
    Submission,
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course_code", "account", "term", "is_public")
    search_fields = ("name", "course_code")
    list_filter = ("account", "term", "is_public")


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course")
    search_fields = ("name", "course__name", "course__course_code")
    list_filter = ("course",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "section",
        "role",
        "enrollment_state",
        "grades",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "section__name",
        "section__course__name",
    )
    list_filter = ("role", "enrollment_state")


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "course", "position", "unlock_at", "require_sequential_progress")
    search_fields = ("name", "course__name")
    list_filter = ("course", "require_sequential_progress")


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "course", "is_published", "is_front_page")
    search_fields = ("title", "body")
    list_filter = ("course", "is_published", "is_front_page")


@admin.register(ModuleItem)
class ModuleItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "module",
        "position",
        "indent",
        "content_type",
        "object_id",
        "completion_requirement",
    )
    list_filter = ("module", "completion_requirement", "content_type")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "course",
        "points_possible",
        "grading_type",
        "due_at",
        "published",
    )
    search_fields = ("title", "description")
    list_filter = ("course", "grading_type", "published")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assignment",
        "user",
        "attempt",
        "score",
        "grade",
        "submitted_at",
        "workflow_state",
    )
    search_fields = ("user__username", "user__email", "assignment__title")
    list_filter = ("assignment", "workflow_state")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assignment",
        "quiz_type",
        "time_limit_minutes",
        "allowed_attempts",
        "shuffle_answers",
    )
    list_filter = ("quiz_type", "shuffle_answers")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "position", "question_type", "points")
    search_fields = ("question_text",)
    list_filter = ("quiz", "question_type")


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "text", "is_correct")
    search_fields = ("text",)
    list_filter = ("question", "is_correct")


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "started_at", "finished_at")
    list_filter = ("started_at", "finished_at")


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "attempt", "question", "selected_choice")
    list_filter = ("question",)

