from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from rest_framework import viewsets

from core.models import Role
from .models import (
    Assignment,
    Choice,
    Course,
    Enrollment,
    EnrollmentState,
    Module,
    ModuleItem,
    Page,
    Question,
    Quiz,
    QuizAttempt,
    Section,
    StudentAnswer,
    Submission,
    SubmissionWorkflowState,
)
from .serializers import (
    AssignmentSerializer,
    ChoiceSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    ModuleItemSerializer,
    ModuleSerializer,
    PageSerializer,
    QuestionSerializer,
    QuizAttemptSerializer,
    QuizSerializer,
    SectionSerializer,
    StudentAnswerSerializer,
    SubmissionSerializer,
)


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("id")
    serializer_class = CourseSerializer


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all().order_by("id")
    serializer_class = SectionSerializer


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all().order_by("-created_at")
    serializer_class = EnrollmentSerializer


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all().order_by("course", "position")
    serializer_class = ModuleSerializer


class PageViewSet(viewsets.ModelViewSet):
    queryset = Page.objects.all().order_by("course", "id")
    serializer_class = PageSerializer


class ModuleItemViewSet(viewsets.ModelViewSet):
    queryset = ModuleItem.objects.all().order_by("module", "position", "id")
    serializer_class = ModuleItemSerializer


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all().order_by("course", "due_at", "id")
    serializer_class = AssignmentSerializer


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all().order_by("assignment", "user", "attempt")
    serializer_class = SubmissionSerializer


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all().order_by("id")
    serializer_class = QuizSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all().order_by("quiz", "position", "id")
    serializer_class = QuestionSerializer


class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all().order_by("question", "id")
    serializer_class = ChoiceSerializer


class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all().order_by("id")
    serializer_class = QuizAttemptSerializer


class StudentAnswerViewSet(viewsets.ModelViewSet):
    queryset = StudentAnswer.objects.all().order_by("attempt", "question_id")
    serializer_class = StudentAnswerSerializer


def _user_is_teacher_for_course(user, course: Course) -> bool:
    if not user.is_authenticated:
        return False
    return Enrollment.objects.filter(
        user=user,
        section__course=course,
        role=Role.TEACHER,
        enrollment_state=EnrollmentState.ACTIVE,
    ).exists()


def submit_assignment(request, assignment_id: int):
    """
    Handle assignment submission (text, URL, file) based on assignment.submission_types.
    Creates a new Submission record and redirects back to the assignment detail page.
    """

    assignment = get_object_or_404(Assignment, id=assignment_id)

    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to submit this assignment.")
        return redirect("course_detail", course_id=assignment.course_id)

    if request.method != "POST":
        return redirect("course_detail", course_id=assignment.course_id)

    # Determine next attempt number
    last_submission = (
        Submission.objects.filter(assignment=assignment, user=request.user)
        .order_by("-attempt")
        .first()
    )
    next_attempt = (last_submission.attempt + 1) if last_submission else 1

    body = request.POST.get("body") or None
    url = request.POST.get("url") or None
    attachment = request.FILES.get("attachment") if request.FILES else None

    submission = Submission.objects.create(
        assignment=assignment,
        user=request.user,
        attempt=next_attempt,
        body=body,
        url=url,
        attachment=attachment,
        submitted_at=timezone.now(),
        workflow_state="submitted",
    )

    messages.success(request, "Your assignment has been submitted.")

    # Redirect back to the module-based assignment detail with confetti flag
    from core.views import module_item_detail  # avoid circular import at top

    # 찾기: 이 assignment를 가리키는 ModuleItem 중 하나 (여러 개면 첫 번째)
    module_item = (
        ModuleItem.objects.filter(
            content_type__model="assignment", object_id=assignment.id
        )
        .select_related("module__course")
        .first()
    )

    if module_item:
        return redirect(
            f"{redirect('module_item_detail', course_id=assignment.course_id, item_id=module_item.id).url}?submitted=1"
        )

    # Fallback: 코스 상세로 이동
    return redirect("course_detail", course_id=assignment.course_id)


def submission_list(request, assignment_id: int):
    """
    Show all submissions for an assignment (teacher view).
    """

    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course

    if not _user_is_teacher_for_course(request.user, course):
        messages.error(request, "You are not allowed to grade this assignment.")
        return redirect("course_detail", course_id=course.id)

    submissions = (
        Submission.objects.filter(assignment=assignment)
        .select_related("user")
        .order_by("user__username", "attempt")
    )

    context = {
        "course": course,
        "assignment": assignment,
        "submissions": submissions,
        "active_tab": "modules",
    }
    return render(request, "courses/submission_list.html", context)


def grade_submission(request, assignment_id: int, submission_id: int):
    """
    SpeedGrader-style view for grading a single submission.
    Allows teacher to set score and feedback, and navigates between students.
    """

    assignment = get_object_or_404(Assignment, id=assignment_id)
    course = assignment.course

    if not _user_is_teacher_for_course(request.user, course):
        messages.error(request, "You are not allowed to grade this assignment.")
        return redirect("course_detail", course_id=course.id)

    submission = get_object_or_404(
        Submission, id=submission_id, assignment=assignment
    )

    # Build ordered list of submissions for navigation
    submissions_qs = Submission.objects.filter(assignment=assignment).order_by(
        "user__username", "id"
    )
    submissions = list(submissions_qs)
    prev_submission = next_submission = None

    try:
        idx = next(i for i, s in enumerate(submissions) if s.id == submission.id)
    except StopIteration:
        idx = None

    if idx is not None:
        if idx > 0:
            prev_submission = submissions[idx - 1]
        if idx < len(submissions) - 1:
            next_submission = submissions[idx + 1]

    if request.method == "POST":
        raw_score = request.POST.get("score")
        feedback = request.POST.get("feedback") or None

        if raw_score:
            try:
                submission.score = Decimal(raw_score)
            except InvalidOperation:
                messages.error(request, "Invalid score value.")
        else:
            submission.score = None

        submission.feedback = feedback
        submission.workflow_state = SubmissionWorkflowState.GRADED
        submission.save()

        messages.success(request, "Grade has been saved.")

        # Redirect back to same grading view (PRG pattern)
        return redirect(
            "grade_submission",
            assignment_id=assignment.id,
            submission_id=submission.id,
        )

    prev_submission_url = (
        None
        if not prev_submission
        else f"/api/courses/assignments/{assignment.id}/submissions/{prev_submission.id}/grade/"
    )
    next_submission_url = (
        None
        if not next_submission
        else f"/api/courses/assignments/{assignment.id}/submissions/{next_submission.id}/grade/"
    )

    context = {
        "course": course,
        "assignment": assignment,
        "submission": submission,
        "prev_submission_url": prev_submission_url,
        "next_submission_url": next_submission_url,
        "active_tab": "modules",
    }
    return render(request, "courses/speedgrader.html", context)

