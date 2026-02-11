from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AssignmentViewSet,
    ChoiceViewSet,
    CourseViewSet,
    EnrollmentViewSet,
    ModuleItemViewSet,
    ModuleViewSet,
    PageViewSet,
    QuestionViewSet,
    QuizAttemptViewSet,
    QuizViewSet,
    SectionViewSet,
    StudentAnswerViewSet,
    SubmissionViewSet,
    grade_submission,
    submission_list,
    submit_assignment,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet)
router.register(r"sections", SectionViewSet)
router.register(r"enrollments", EnrollmentViewSet)
router.register(r"modules", ModuleViewSet)
router.register(r"pages", PageViewSet)
router.register(r"module-items", ModuleItemViewSet)
router.register(r"assignments", AssignmentViewSet)
router.register(r"submissions", SubmissionViewSet)
router.register(r"quizzes", QuizViewSet)
router.register(r"questions", QuestionViewSet)
router.register(r"choices", ChoiceViewSet)
router.register(r"quiz-attempts", QuizAttemptViewSet)
router.register(r"student-answers", StudentAnswerViewSet)

urlpatterns = [
    path(
        "assignments/<int:assignment_id>/submit/",
        submit_assignment,
        name="submit_assignment",
    ),
    path(
        "assignments/<int:assignment_id>/submissions/",
        submission_list,
        name="submission_list",
    ),
    path(
        "assignments/<int:assignment_id>/submissions/<int:submission_id>/grade/",
        grade_submission,
        name="grade_submission",
    ),
]

urlpatterns += router.urls

