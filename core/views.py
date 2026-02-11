import json

from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework import viewsets

from courses.models import Assignment, Course, Module, ModuleItem, Page, Submission
from courses.views import _user_is_teacher_for_course
from .models import Account, Term, User, Video, VideoProgress
from .serializers import AccountSerializer, TermSerializer, UserSerializer


class LogoutViewAllowGet(auth_views.LogoutView):
    """LogoutView that accepts GET so /accounts/logout/ works from address bar or link."""

    http_method_names = ["get", "post", "options"]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = Account.objects.all().order_by("id")
    serializer_class = AccountSerializer


class TermViewSet(viewsets.ModelViewSet):
    queryset = Term.objects.all().order_by("start_date", "end_date")
    serializer_class = TermSerializer


def course_catalog(request):
    """
    수강신청 목록 페이지. 전체 강의 표시.
    이미 수강 중인 강의는 버튼 비활성화.
    """
    from courses.models import Course, Enrollment

    courses = Course.objects.select_related("term").prefetch_related(
        "sections__enrollments",
    ).all()

    enrolled_course_ids = set()
    if request.user.is_authenticated:
        enrolled_course_ids = set(
            Enrollment.objects.filter(
                user=request.user,
                section__course__in=courses,
            ).values_list("section__course_id", flat=True)
        )

    course_list = []
    for course in courses:
        teacher = (
            Enrollment.objects.filter(
                section__course=course,
                role="teacher",
            )
            .select_related("user")
            .first()
        )
        teacher_name = (
            teacher.user.get_full_name() or teacher.user.username
            if teacher
            else "-"
        )
        course_list.append({
            "course": course,
            "teacher": teacher_name,
            "is_enrolled": course.id in enrolled_course_ids,
        })

    context = {
        "course_list": course_list,
    }
    return render(request, "courses/course_catalog.html", context)


@login_required
def enroll_course(request, course_id: int):
    """
    특정 강의에 학생 등록. POST 전용.
    """
    from django.contrib import messages
    from courses.models import Course, Enrollment, EnrollmentState, Section
    from core.models import Role

    if request.method != "POST":
        return redirect("course_catalog")

    course = get_object_or_404(Course, id=course_id)
    section = Section.objects.filter(course=course).first()

    if not section:
        messages.error(request, "이 강의에는 등록할 수 있는 분반이 없습니다.")
        return redirect("course_catalog")

    existing = Enrollment.objects.filter(
        user=request.user,
        section=section,
    ).exists()

    if existing:
        messages.info(request, "이미 수강 중인 강의입니다.")
        return redirect("dashboard")

    Enrollment.objects.create(
        user=request.user,
        section=section,
        role=Role.STUDENT,
        enrollment_state=EnrollmentState.ACTIVE,
    )

    messages.success(request, "수강신청이 완료되었습니다.")
    return redirect("dashboard")


def signup(request):
    """
    회원가입. 가입 성공 시 자동 로그인 후 대시보드로 이동.
    """
    from .forms import SignUpForm

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend",
            )
            return redirect("dashboard")
    else:
        form = SignUpForm()

    return render(request, "registration/signup.html", {"form": form})


@login_required
def dashboard(request):
    """
    Simple dashboard view.
    For now, it shows all courses as Canvas-like course cards.
    """

    courses = Course.objects.select_related("term").all()
    context = {
        "courses": courses,
    }
    return render(request, "dashboard.html", context)


@login_required
def course_detail(request, course_id: int):
    """
    Course detail view with modules list, similar to Canvas course home.
    """

    course = get_object_or_404(Course, id=course_id)
    modules = (
        Module.objects.filter(course=course)
        .prefetch_related("items__content_type")
        .order_by("position", "id")
    )

    context = {
        "course": course,
        "modules": modules,
        "active_tab": "modules",
    }
    return render(request, "courses/course_home.html", context)


def _get_sequence_neighbors(course: Course, current_item: ModuleItem):
    """
    Given a course and current ModuleItem, find previous and next items
    in the course-wide module sequence.
    """

    items = list(
        ModuleItem.objects.filter(module__course=course)
        .select_related("module")
        .order_by("module__position", "module_id", "position", "id")
    )
    prev_item = next_item = None

    try:
        index = next(i for i, it in enumerate(items) if it.id == current_item.id)
    except StopIteration:
        return None, None

    if index > 0:
        prev_item = items[index - 1]
    if index < len(items) - 1:
        next_item = items[index + 1]

    return prev_item, next_item


@login_required
def module_item_detail(request, course_id: int, item_id: int):
    """
    Show the detail of a ModuleItem's underlying content (Page or Assignment),
    with Canvas-like sequence navigation (Previous / Next).
    """

    course = get_object_or_404(Course, id=course_id)
    module_item = get_object_or_404(
        ModuleItem, id=item_id, module__course=course
    )
    content = module_item.content_object

    prev_item, next_item = _get_sequence_neighbors(course, module_item)

    latest_submission = None
    if request.user.is_authenticated and isinstance(content, Assignment):
        latest_submission = (
            Submission.objects.filter(assignment=content, user=request.user)
            .order_by("-attempt", "-submitted_at", "-id")
            .first()
        )

    prev_item_url = (
        reverse("module_item_detail", args=[course.id, prev_item.id])
        if prev_item
        else None
    )
    next_item_url = (
        reverse("module_item_detail", args=[course.id, next_item.id])
        if next_item
        else None
    )

    is_teacher = (
        request.user.is_authenticated
        and (
            request.user.is_staff
            or _user_is_teacher_for_course(request.user, course)
        )
    )
    context_base = {
        "course": course,
        "module_item": module_item,
        "prev_item_url": prev_item_url,
        "next_item_url": next_item_url,
        "active_tab": "modules",
        "latest_submission": latest_submission,
        "is_teacher": is_teacher,
    }

    # Route to appropriate template based on underlying model
    if isinstance(content, Page):
        context = {
            **context_base,
            "page": content,
        }
        template_name = "courses/course_page.html"
    elif isinstance(content, Assignment):
        context = {
            **context_base,
            "assignment": content,
        }
        template_name = "courses/assignment_detail.html"
    else:
        # Fallback: simple generic view
        context = {
            **context_base,
            "object": content,
        }
        template_name = "courses/course_page.html"

    return render(request, template_name, context)


@login_required
def video_list(request, course_id: int):
    """
    강의별 동영상 목록 (강의 목차 임시 연결용).
    """
    course = get_object_or_404(Course, id=course_id)
    videos = Video.objects.filter(course=course).order_by("id")

    context = {
        "course": course,
        "videos": videos,
        "active_tab": "modules",
    }
    return render(request, "courses/video_list.html", context)


@login_required
def video_detail(request, video_id: int):
    """
    비디오 플레이어 화면. 진도율 및 출석 상태 실시간 표시.
    """
    video = get_object_or_404(Video, id=video_id)
    course = video.course

    progress = VideoProgress.objects.filter(
        user=request.user,
        video=video,
    ).first()

    duration = video.duration or 1
    watched = progress.watched_time if progress else 0
    progress_percent = round(watched / duration * 100, 1)
    progress_status = "완료" if (progress and progress.is_completed) else "미완료"

    context = {
        "course": course,
        "video": video,
        "progress": progress,
        "video_src": video.get_src_url(),
        "progress_percent": progress_percent,
        "progress_status": progress_status,
        "active_tab": "modules",
    }
    return render(request, "courses/video_detail.html", context)


@login_required
@require_POST
def update_progress(request):
    """
    JS가 주기적으로 호출하는 API.
    JSON body: video_id, watched_time(초), duration(초)
    (watched_time / duration) * 100 로 진도율 계산.
    watched_time >= duration * 0.95 이면 is_completed = True.
    """
    print(f"Update request: {request.body}")

    try:
        data = json.loads(request.body)
        video_id = int(data.get("video_id", 0))
        watched_time = float(data.get("watched_time", 0))
        duration = float(data.get("duration", 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"error": "Invalid parameters"}, status=400)

    video = get_object_or_404(Video, id=video_id)

    if duration <= 0:
        duration = video.duration or 1

    if watched_time < 0:
        watched_time = 0

    progress, _ = VideoProgress.objects.get_or_create(
        user=request.user,
        video=video,
        defaults={"watched_time": 0, "is_completed": False},
    )

    progress.watched_time = max(progress.watched_time, watched_time)

    if duration > 0 and progress.watched_time >= duration * 0.95:
        progress.is_completed = True

    progress.save()

    progress_percent = int((progress.watched_time / duration) * 100) if duration > 0 else 0
    progress_percent = min(100, progress_percent)

    return JsonResponse({
        "status": "success",
        "progress": progress_percent,
        "percent": progress_percent,
        "watched_time": progress.watched_time,
        "is_completed": progress.is_completed,
    })

