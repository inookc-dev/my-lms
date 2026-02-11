from rest_framework import serializers

from .models import Account, Term, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "sis_id",
            "first_name",
            "last_name",
            "avatar_url",
            "time_zone",
            "is_staff",
            "is_active",
            "date_joined",
            "last_login",
        ]
        read_only_fields = ["id", "is_staff", "is_active", "date_joined", "last_login"]


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = "__all__"

