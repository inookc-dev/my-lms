from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import Account, Role, Term


class Course(models.Model):
    """
    Canvas의 Course에 해당하는 강의 단위.
    - 특정 Account(또는 Sub-account)에 속함
    - 특정 Term(학기)에 속함
    """

    account = models.ForeignKey(
        Account,
        related_name="courses",
        on_delete=models.CASCADE,
        help_text="이 강의가 속한 계정(또는 하위 계정)",
    )
    term = models.ForeignKey(
        Term,
        related_name="courses",
        on_delete=models.PROTECT,
        help_text="이 강의가 열리는 학기",
    )
    name = models.CharField(max_length=255)
    course_code = models.CharField(
        max_length=50,
        help_text="강의 코드(예: CS101, ENG-202 등)",
    )
    is_public = models.BooleanField(
        default=False,
        help_text="공개 강의 여부 (예: 카탈로그에 노출할지 여부)",
    )

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self) -> str:
        return f"{self.name} ({self.course_code})"


class Section(models.Model):
    """
    분반 단위.
    - 하나의 Course는 여러 Section을 가질 수 있음(1:N)
    - 학생은 Course가 아닌 Section에 등록됨
    """

    course = models.ForeignKey(
        Course,
        related_name="sections",
        on_delete=models.CASCADE,
        help_text="이 분반이 속한 강의",
    )
    name = models.CharField(
        max_length=255,
        help_text="분반 이름(예: 001반, A반 등)",
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Enrollment",
        related_name="enrolled_sections",
        blank=True,
        help_text="이 분반에 수강 등록된 학생들",
    )

    class Meta:
        verbose_name = "Section"
        verbose_name_plural = "Sections"

    def __str__(self) -> str:
        return f"{self.course} - {self.name}"


class EnrollmentState(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    CONCLUDED = "concluded", "Concluded"
    PENDING = "pending", "Pending"


class Enrollment(models.Model):
    """
    User와 Section을 연결하는 중계(Enrollment) 모델.
    - 한 사용자(User)가 섹션마다 다른 역할(Student/Teacher 등)을 가질 수 있음.
    - 학생은 Course가 아니라 Section에 등록됨.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="enrollments",
        on_delete=models.CASCADE,
        help_text="이 등록 레코드의 사용자",
    )
    section = models.ForeignKey(
        Section,
        related_name="enrollments",
        on_delete=models.CASCADE,
        help_text="사용자가 등록된 분반",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        help_text="이 섹션에서의 역할 (Student, Teacher 등)",
    )
    enrollment_state = models.CharField(
        max_length=20,
        choices=EnrollmentState.choices,
        default=EnrollmentState.PENDING,
        help_text="등록 상태",
    )
    grades = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="현재 점수/성적 (선택 사항, 예: 95.50, 3.70 등)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Enrollment"
        verbose_name_plural = "Enrollments"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "section"],
                name="unique_user_section_enrollment",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.section} ({self.role})"


class Module(models.Model):
    """
    코스 내 학습 흐름을 나누는 모듈.
    - Course에 종속
    - position: 코스 안에서의 모듈 순서
    - prerequisites: 선행 모듈 (self-referencing M2M)
    """

    course = models.ForeignKey(
        "Course",
        related_name="modules",
        on_delete=models.CASCADE,
        help_text="이 모듈이 속한 강의",
    )
    name = models.CharField(
        max_length=255,
        help_text="모듈 이름 (예: Week 1, Introduction 등)",
    )
    position = models.PositiveIntegerField(
        default=0,
        help_text="코스 내 모듈 순서",
    )
    unlock_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="이 날짜/시간 이후에 모듈이 열림",
    )
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="dependent_modules",
        blank=True,
        help_text="이 모듈이 열리기 전에 완료되어야 하는 선행 모듈들",
    )
    require_sequential_progress = models.BooleanField(
        default=False,
        help_text="학생이 이 모듈의 아이템을 순서대로만 진행해야 하는지 여부",
    )

    class Meta:
        ordering = ["course", "position", "id"]
        verbose_name = "Module"
        verbose_name_plural = "Modules"

    def __str__(self) -> str:
        return f"{self.course} / {self.name}"


class Page(models.Model):
    """
    코스 내 위키 페이지.
    - 텍스트/이미지/비디오 등을 포함하는 HTML 페이지
    """

    course = models.ForeignKey(
        "Course",
        related_name="pages",
        on_delete=models.CASCADE,
        help_text="이 페이지가 속한 강의",
    )
    title = models.CharField(max_length=255)
    body = models.TextField(
        help_text="HTML 형태로 저장되는 페이지 본문",
    )
    is_published = models.BooleanField(
        default=False,
        help_text="학생에게 공개 여부",
    )
    is_front_page = models.BooleanField(
        default=False,
        help_text="코스 홈(Front Page)로 사용할지 여부",
    )

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        constraints = [
            models.UniqueConstraint(
                fields=["course"],
                condition=models.Q(is_front_page=True),
                name="unique_front_page_per_course",
            )
        ]

    def __str__(self) -> str:
        return f"{self.course} / {self.title}"


class GradingType(models.TextChoices):
    """
    과제 채점 방식.
    Canvas Instructor Guide 기준:
    - pass_fail, percent, letter_grade, points
    """

    PASS_FAIL = "pass_fail", "Pass / Fail"
    PERCENT = "percent", "Percent"
    LETTER_GRADE = "letter_grade", "Letter grade"
    POINTS = "points", "Points"


class Assignment(models.Model):
    """
    코스 내 과제.
    - Course에 종속
    - 여러 제출(Submission)을 가질 수 있음
    """

    course = models.ForeignKey(
        Course,
        related_name="assignments",
        on_delete=models.CASCADE,
        help_text="이 과제가 속한 강의",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(
        help_text="과제 설명 (리치 텍스트 / HTML 등)",
    )
    points_possible = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="배점 (소수점 둘째 자리까지, 예: 100.00, 10.50)",
    )
    due_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="마감일",
    )
    unlock_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="과제를 열어두는 시작 시각",
    )
    lock_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="과제가 완전히 닫히는 시각",
    )
    # 제출 유형: 문자열 리스트를 JSON으로 저장
    # 예: ["online_text_entry", "online_upload"]
    submission_types = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            "허용되는 제출 유형 리스트. "
            "예: ['online_text_entry', 'online_upload', 'online_url', "
            "'media_recording', 'none']"
        ),
    )
    grading_type = models.CharField(
        max_length=20,
        choices=GradingType.choices,
        default=GradingType.POINTS,
        help_text="채점 방식 (pass_fail, percent, letter_grade, points)",
    )
    published = models.BooleanField(
        default=False,
        help_text="학생에게 과제가 공개되었는지 여부",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Assignment"
        verbose_name_plural = "Assignments"
        ordering = ["course", "due_at", "id"]

    def __str__(self) -> str:
        return f"{self.course} / {self.title}"


class SubmissionWorkflowState(models.TextChoices):
    """
    제출 상태.
    Canvas Student Guide 기준:
    - submitted, graded, unsubmitted, late, missing
    """

    SUBMITTED = "submitted", "Submitted"
    GRADED = "graded", "Graded"
    UNSUBMITTED = "unsubmitted", "Unsubmitted"
    LATE = "late", "Late"
    MISSING = "missing", "Missing"


class Submission(models.Model):
    """
    과제 제출 모델.
    - Assignment와 User를 연결
    - 한 Assignment에 대해 여러 번(여러 attempt) 제출 가능
    """

    assignment = models.ForeignKey(
        Assignment,
        related_name="submissions",
        on_delete=models.CASCADE,
        help_text="제출 대상 과제",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="submissions",
        on_delete=models.CASCADE,
        help_text="제출한 사용자",
    )
    attempt = models.PositiveIntegerField(
        default=1,
        help_text="제출 시도 횟수 (1부터 시작)",
    )

    # 제출 내용
    body = models.TextField(
        null=True,
        blank=True,
        help_text="온라인 텍스트 입력 내용",
    )
    url = models.URLField(
        null=True,
        blank=True,
        help_text="온라인 URL 제출 (예: Git 리포지토리, 외부 페이지 링크)",
    )
    attachment = models.FileField(
        upload_to="submissions/",
        null=True,
        blank=True,
        help_text="파일 업로드 제출",
    )

    # 평가/상태
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="획득 점수",
    )
    grade = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="등급 표기 (예: A, B+, 95%)",
    )
    feedback = models.TextField(
        null=True,
        blank=True,
        help_text="Instructor feedback for this submission",
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="실제 제출 시각",
    )
    workflow_state = models.CharField(
        max_length=20,
        choices=SubmissionWorkflowState.choices,
        default=SubmissionWorkflowState.UNSUBMITTED,
        help_text="제출 상태 (submitted, graded, unsubmitted, late, missing)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Submission"
        verbose_name_plural = "Submissions"
        ordering = ["assignment", "user", "attempt"]
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "user", "attempt"],
                name="unique_assignment_user_attempt",
            )
        ]

    def __str__(self) -> str:
        return f"{self.assignment} / {self.user} (attempt {self.attempt})"


class QuizType(models.TextChoices):
    """
    퀴즈 유형.
    Canvas Basics Guide 기준:
    - graded_quiz, practice_quiz, graded_survey, ungraded_survey
    """

    GRADED_QUIZ = "graded_quiz", "Graded quiz"
    PRACTICE_QUIZ = "practice_quiz", "Practice quiz"
    GRADED_SURVEY = "graded_survey", "Graded survey"
    UNGRADED_SURVEY = "ungraded_survey", "Ungraded survey"


class Quiz(models.Model):
    """
    퀴즈 설정.
    - Assignment와 1:1 관계 (퀴즈도 과제의 일종)
    """

    assignment = models.OneToOneField(
        Assignment,
        related_name="quiz",
        on_delete=models.CASCADE,
        help_text="이 퀴즈가 연결된 과제",
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="제한 시간(분 단위). 비워두면 시간 제한 없음",
    )
    allowed_attempts = models.IntegerField(
        default=-1,
        help_text="허용 시도 횟수. -1은 무제한",
    )
    shuffle_answers = models.BooleanField(
        default=False,
        help_text="문항의 보기를 섞을지 여부",
    )
    quiz_type = models.CharField(
        max_length=20,
        choices=QuizType.choices,
        default=QuizType.GRADED_QUIZ,
        help_text="퀴즈 유형 (graded_quiz, practice_quiz 등)",
    )

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self) -> str:
        return f"Quiz for {self.assignment}"


class QuestionType(models.TextChoices):
    """
    문제 유형.
    - multiple_choice, true_false, short_answer, essay
    """

    MULTIPLE_CHOICE = "multiple_choice", "Multiple choice"
    TRUE_FALSE = "true_false", "True / False"
    SHORT_ANSWER = "short_answer", "Short answer"
    ESSAY = "essay", "Essay"


class Question(models.Model):
    """
    퀴즈 문항.
    - Quiz와 1:N 관계
    """

    quiz = models.ForeignKey(
        Quiz,
        related_name="questions",
        on_delete=models.CASCADE,
        help_text="이 문항이 속한 퀴즈",
    )
    question_text = models.TextField(
        help_text="문제 내용 (HTML 가능)",
    )
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE,
        help_text="문제 유형",
    )
    points = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1,
        help_text="이 문항의 배점",
    )
    position = models.PositiveIntegerField(
        default=0,
        help_text="퀴즈 내 문항 순서",
    )

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["quiz", "position", "id"]

    def __str__(self) -> str:
        return f"{self.quiz} Q{self.position}"


class Choice(models.Model):
    """
    객관식 보기.
    - Question과 1:N 관계
    """

    question = models.ForeignKey(
        Question,
        related_name="choices",
        on_delete=models.CASCADE,
        help_text="이 보기가 속한 문항",
    )
    text = models.CharField(
        max_length=255,
        help_text="보기 내용",
    )
    is_correct = models.BooleanField(
        default=False,
        help_text="정답 여부",
    )

    class Meta:
        verbose_name = "Choice"
        verbose_name_plural = "Choices"

    def __str__(self) -> str:
        return f"{self.question} - {self.text} ({'correct' if self.is_correct else 'incorrect'})"


class QuizAttempt(models.Model):
    """
    퀴즈 응시 기록.
    - Submission과 1:1 관계로, 각 제출이 하나의 퀴즈 시도에 대응
    - 실제 시도 번호는 Submission.attempt에 저장됨
    """

    submission = models.OneToOneField(
        Submission,
        related_name="quiz_attempt",
        on_delete=models.CASCADE,
        help_text="이 퀴즈 시도에 대응하는 과제 제출",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="퀴즈를 시작한 시각",
    )
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="퀴즈를 완료한 시각",
    )

    class Meta:
        verbose_name = "Quiz attempt"
        verbose_name_plural = "Quiz attempts"

    def __str__(self) -> str:
        return f"Attempt {self.submission.attempt} for {self.submission.assignment} by {self.submission.user}"


class StudentAnswer(models.Model):
    """
    학생 답안.
    - QuizAttempt와 Question을 연결
    - 객관식(selected_choice) 또는 주관식(text_response) 모두 지원
    """

    attempt = models.ForeignKey(
        QuizAttempt,
        related_name="answers",
        on_delete=models.CASCADE,
        help_text="이 답안이 속한 퀴즈 시도",
    )
    question = models.ForeignKey(
        Question,
        related_name="student_answers",
        on_delete=models.CASCADE,
        help_text="답을 작성한 문항",
    )
    selected_choice = models.ForeignKey(
        Choice,
        related_name="selected_answers",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="객관식 선택지 (해당되는 경우에만)",
    )
    text_response = models.TextField(
        null=True,
        blank=True,
        help_text="주관식/서술형 답변 내용",
    )

    class Meta:
        verbose_name = "Student answer"
        verbose_name_plural = "Student answers"
        ordering = ["attempt", "question_id"]

    def __str__(self) -> str:
        return f"Answer by {self.attempt.submission.user} for {self.question}"

class CompletionRequirement(models.TextChoices):
    """
    모듈 아이템 완료 조건.
    Canvas Student Guide 의 must_view / must_submit / min_score 등.
    """

    MUST_VIEW = "must_view", "Must view"
    MUST_SUBMIT = "must_submit", "Must submit"
    MIN_SCORE = "min_score", "Minimum score"


class ModuleItem(models.Model):
    """
    모듈 안에 들어가는 개별 아이템.
    - Module과 1:N
    - Page, Assignment, Quiz, File, ExternalUrl 등을 GenericForeignKey로 연결
    """

    module = models.ForeignKey(
        Module,
        related_name="items",
        on_delete=models.CASCADE,
        help_text="이 아이템이 속한 모듈",
    )
    position = models.PositiveIntegerField(
        default=0,
        help_text="모듈 내 아이템 순서",
    )
    indent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text="모듈 내 들여쓰기 레벨 (0~5)",
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        help_text="연결된 객체 타입 (Page, Assignment 등)",
    )
    object_id = models.PositiveIntegerField(
        help_text="연결된 객체의 PK",
    )
    content_object = GenericForeignKey("content_type", "object_id")
    completion_requirement = models.CharField(
        max_length=20,
        choices=CompletionRequirement.choices,
        null=True,
        blank=True,
        help_text="이 아이템의 완료 조건 (must_view, must_submit, min_score 등)",
    )

    class Meta:
        ordering = ["module", "position", "id"]
        verbose_name = "Module item"
        verbose_name_plural = "Module items"

    def __str__(self) -> str:
        return f"{self.module} :: {self.content_object} (pos={self.position})"

