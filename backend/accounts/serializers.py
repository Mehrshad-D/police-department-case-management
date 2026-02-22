"""
User and Role serializers. Registration with unique username, email, phone, national_id.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Role

User = get_user_model()


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserListSerializer(serializers.ModelSerializer):
    roles = RoleSerializer(many=True, read_only=True)
    role_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'full_name', 'national_id',
            'is_active', 'roles', 'role_names', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']

    def get_role_names(self, obj):
        return obj.role_names()


class UserCreateSerializer(serializers.ModelSerializer):
    """Registration: username, password, email, phone, full_name, national_id. All unique."""
    password = serializers.CharField(write_only=True, min_length=8)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'email', 'phone', 'full_name', 'national_id',
            'role_ids',
        ]
        extra_kwargs = {
            'email': {'required': True},
            'phone': {'required': True},
            'full_name': {'required': True},
            'national_id': {'required': True},
        }

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('A user with this username already exists.')
        return value

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError('Email is required.')
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_phone(self, value):
        if not value:
            raise serializers.ValidationError('Phone is required.')
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError('A user with this phone already exists.')
        return value

    def validate_national_id(self, value):
        if not value:
            raise serializers.ValidationError('National ID is required.')
        if User.objects.filter(national_id=value).exists():
            raise serializers.ValidationError('A user with this national ID already exists.')
        return value

    def create(self, validated_data):
        role_ids = validated_data.pop('role_ids', [])
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data, password=password)
        if role_ids:
            user.roles.set(Role.objects.filter(pk__in=role_ids))
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Update user; admin can set role_ids."""
    role_ids = serializers.ListField(child=serializers.IntegerField(), required=False, write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'full_name', 'national_id',
            'is_active', 'role_ids',
        ]

    def update(self, instance, validated_data):
        role_ids = validated_data.pop('role_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if role_ids is not None:
            instance.roles.set(Role.objects.filter(pk__in=role_ids))
        return instance


class LoginSerializer(serializers.Serializer):
    """Login with password + one identifier (username, national_id, phone, or email)."""
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        identifier = data.get('identifier', '').strip()
        password = data.get('password')
        if not identifier or not password:
            raise serializers.ValidationError('Identifier and password are required.')
        User = get_user_model()
        user = (
            User.objects.filter(username=identifier).first()
            or User.objects.filter(national_id=identifier).first()
            or User.objects.filter(phone=identifier).first()
            or User.objects.filter(email__iexact=identifier).first()
        )
        if not user or not user.check_password(password):
            raise serializers.ValidationError('Invalid identifier or password.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        data['user'] = user
        return data
