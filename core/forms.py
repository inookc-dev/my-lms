from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignUpForm(UserCreationForm):
    """
    회원가입 폼. 이메일을 ID로 사용.
    """

    is_instructor = forms.BooleanField(
        required=False,
        initial=False,
        label="선생님 계정으로 가입",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = User
        fields = ("username", "first_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "이메일 (ID)"
        self.fields["username"].help_text = None
        self.fields["username"].widget = forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "example@email.com",
        })
        self.fields["first_name"].label = "이름"
        self.fields["first_name"].required = True
        self.fields["first_name"].widget.attrs.setdefault("class", "form-control")
        self.fields["password1"].label = "비밀번호"
        self.fields["password1"].widget.attrs.setdefault("class", "form-control")
        self.fields["password2"].label = "비밀번호 확인"
        self.fields["password2"].widget.attrs.setdefault("class", "form-control")

    def clean_username(self):
        """username = 이메일. 이메일 형식 검증."""
        email = self.cleaned_data.get("username", "").strip().lower()
        if not email:
            raise forms.ValidationError("이메일을 입력해주세요.")
        if "@" not in email or "." not in email:
            raise forms.ValidationError("올바른 이메일 형식을 입력해주세요.")
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["username"].strip().lower()
        user.username = email
        user.email = email
        user.is_staff = self.cleaned_data.get("is_instructor", False)
        if commit:
            user.save()
        return user
