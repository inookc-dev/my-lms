from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Account, Role, Term, Video
from courses.models import (
    Assignment,
    Course,
    Enrollment,
    EnrollmentState,
    GradingType,
    Module,
    ModuleItem,
    Page,
    Quiz,
    QuizType,
    Section,
)


class Command(BaseCommand):
    help = "Seed initial data for development (users, courses, enrollments, and sample content)."

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.MIGRATE_HEADING("Seeding initial data..."))

        # 1. Users
        teacher, _ = User.objects.get_or_create(
            email="teacher@example.com",
            defaults={
                "username": "teacher",
                "first_name": "Canvas",
                "last_name": "Teacher",
                "time_zone": "UTC",
                "is_staff": True,
            },
        )
        teacher.set_password("1234")
        teacher.save()

        students = []
        for i in range(1, 6):
            email = f"student{i}@example.com"
            username = f"student{i}"
            student, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": username,
                    "first_name": "Student",
                    "last_name": str(i),
                    "time_zone": "UTC",
                },
            )
            student.set_password("1234")
            student.save()
            students.append(student)

        self.stdout.write(self.style.SUCCESS("Users created/updated."))

        # 2. Account & Term
        root_account, _ = Account.objects.get_or_create(
            name="Main Account",
            parent=None,
        )

        default_term, _ = Term.objects.get_or_create(
            name="Default Term",
            defaults={
                "start_date": date(timezone.now().year, 1, 1),
                "end_date": date(timezone.now().year, 12, 31),
            },
        )

        # 3. Courses
        history_course, _ = Course.objects.get_or_create(
            name="History 101: American History",
            course_code="HIST101",
            defaults={
                "account": root_account,
                "term": default_term,
                "is_public": True,
            },
        )
        biology_course, _ = Course.objects.get_or_create(
            name="Biology 101",
            course_code="BIO101",
            defaults={
                "account": root_account,
                "term": default_term,
                "is_public": True,
            },
        )

        # 4. Sections
        history_section, _ = Section.objects.get_or_create(
            course=history_course,
            name="History 101 - Section 1",
        )
        biology_section, _ = Section.objects.get_or_create(
            course=biology_course,
            name="Biology 101 - Section 1",
        )

        # 5. Enrollments (teacher + students in both courses)
        from courses.models import EnrollmentState  # noqa

        # Teacher as TEACHER in both sections
        Enrollment.objects.get_or_create(
            user=teacher,
            section=history_section,
            defaults={
                "role": Role.TEACHER,
                "enrollment_state": EnrollmentState.ACTIVE,
            },
        )
        Enrollment.objects.get_or_create(
            user=teacher,
            section=biology_section,
            defaults={
                "role": Role.TEACHER,
                "enrollment_state": EnrollmentState.ACTIVE,
            },
        )

        # Students as STUDENT in both sections
        for student in students:
            Enrollment.objects.get_or_create(
                user=student,
                section=history_section,
                defaults={
                    "role": Role.STUDENT,
                    "enrollment_state": EnrollmentState.ACTIVE,
                },
            )
            Enrollment.objects.get_or_create(
                user=student,
                section=biology_section,
                defaults={
                    "role": Role.STUDENT,
                    "enrollment_state": EnrollmentState.ACTIVE,
                },
            )

        self.stdout.write(self.style.SUCCESS("Enrollments created."))

        # 6. Modules for History 101
        week1, _ = Module.objects.get_or_create(
            course=history_course,
            name="Week 1: Introduction",
            defaults={"position": 1},
        )
        week2, _ = Module.objects.get_or_create(
            course=history_course,
            name="Week 2: Revolution",
            defaults={"position": 2},
        )

        # 7. Pages for History 101
        syllabus_page, _ = Page.objects.get_or_create(
            course=history_course,
            title="Course Syllabus",
            defaults={
                "body": "<h1>Course Syllabus</h1><p>Welcome to History 101.</p>",
                "is_published": True,
                "is_front_page": True,
            },
        )
        welcome_page, _ = Page.objects.get_or_create(
            course=history_course,
            title="Welcome to History",
            defaults={
                "body": "<h1>Welcome to History</h1><p>Let's begin our journey.</p>",
                "is_published": True,
                "is_front_page": False,
            },
        )

        # 8. Assignments for History 101
        position_paper, _ = Assignment.objects.get_or_create(
            course=history_course,
            title="Position Paper",
            defaults={
                "description": "Write a position paper on a key event in American history.",
                "points_possible": 10.00,
                "submission_types": ["online_text_entry", "online_upload"],
                "grading_type": GradingType.POINTS,
                "published": True,
            },
        )

        revolution_quiz_assignment, _ = Assignment.objects.get_or_create(
            course=history_course,
            title="Revolution Quiz",
            defaults={
                "description": "Quiz on the American Revolution.",
                "points_possible": 10.00,
                "submission_types": ["online_quiz", "online_upload"],
                "grading_type": GradingType.POINTS,
                "published": True,
            },
        )

        # 9. Quiz object for "Revolution Quiz"
        quiz, _ = Quiz.objects.get_or_create(
            assignment=revolution_quiz_assignment,
            defaults={
                "quiz_type": QuizType.GRADED_QUIZ,
                "time_limit_minutes": 30,
                "allowed_attempts": 3,
                "shuffle_answers": True,
            },
        )

        # 10. Link content into modules via ModuleItem
        page_ct = ContentType.objects.get_for_model(Page)
        assignment_ct = ContentType.objects.get_for_model(Assignment)

        # Week 1: Syllabus + Position Paper
        ModuleItem.objects.get_or_create(
            module=week1,
            content_type=page_ct,
            object_id=syllabus_page.id,
            defaults={
                "position": 1,
                "indent": 0,
            },
        )
        ModuleItem.objects.get_or_create(
            module=week1,
            content_type=assignment_ct,
            object_id=position_paper.id,
            defaults={
                "position": 2,
                "indent": 0,
            },
        )

        # Week 2: Welcome page + Revolution Quiz
        ModuleItem.objects.get_or_create(
            module=week2,
            content_type=page_ct,
            object_id=welcome_page.id,
            defaults={
                "position": 1,
                "indent": 0,
            },
        )
        ModuleItem.objects.get_or_create(
            module=week2,
            content_type=assignment_ct,
            object_id=revolution_quiz_assignment.id,
            defaults={
                "position": 2,
                "indent": 0,
            },
        )

        self.stdout.write(self.style.SUCCESS("Content (modules, pages, assignments, quiz) created."))

        # 11. Test videos for K-LMS 동영상 진도율
        sample_video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
        Video.objects.get_or_create(
            course=history_course,
            title="테스트 동영상: For Bigger Blazes",
            defaults={
                "video_url": sample_video_url,
                "duration": 15,
            },
        )
        Video.objects.get_or_create(
            course=history_course,
            title="테스트 동영상: Big Buck Bunny (샘플)",
            defaults={
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "duration": 596,
            },
        )

        self.stdout.write(self.style.SUCCESS("Videos created."))
        self.stdout.write(self.style.SUCCESS("Seed data creation completed."))

