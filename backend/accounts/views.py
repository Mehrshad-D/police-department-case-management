"""
Auth: register, login (password + identifier). Roles CRUD (admin).
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import get_user_model

from .models import Role
from .serializers import (
    RoleSerializer,
    UserListSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    LoginSerializer,
)
from .permissions import IsSystemAdmin, IsOfficerOrAbove
from core.utils import log_audit

User = get_user_model()


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class RegisterView(APIView):
    """Public registration. Roles assigned by admin later or via role_ids if caller is admin."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_audit(user, 'create', 'User', user.pk, f'User registered: {user.username}')
        return Response(
            {'success': True, 'data': UserListSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Login with identifier (username, national_id, phone, or email) + password. Returns JWT."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)
        return Response({
            'success': True,
            'data': {
                'user': UserListSerializer(user).data,
                'tokens': tokens,
            },
        })


class UserListView(generics.ListAPIView):
    """List users (admin)."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated, IsSystemAdmin]
    filterset_fields = ['is_active', 'username', 'email']


class DetectivesListView(generics.ListAPIView):
    """List users with Detective role (for assigning detective to a case). Officer+ can call."""
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]

    def get_queryset(self):
        return User.objects.filter(roles__name__iexact='Detective').distinct().order_by('username')


class SuspectCandidatesListView(generics.ListAPIView):
    """List active users for the 'add suspect' dropdown. Detective/Officer+ can call (not admin-only)."""
    serializer_class = UserListSerializer
    permission_classes = [IsAuthenticated, IsOfficerOrAbove]

    def get_queryset(self):
        return User.objects.filter(is_active=True).order_by('username')


class UserDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve/update user. Only System Administrator can update users and assign roles."""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserListSerializer

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH') and self.request.user.has_role('System Administrator'):
            return UserUpdateSerializer
        return UserListSerializer

    def get_queryset(self):
        if self.request.user.has_role('System Administrator'):
            return User.objects.all()
        return User.objects.filter(pk=self.request.user.pk)

    def perform_update(self, serializer):
        if not self.request.user.has_role('System Administrator'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only System Administrator can update users.')
        serializer.save()


class RoleListCreateView(generics.ListCreateAPIView):
    """List and create roles (admin). Add/remove/modify roles without code change."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsSystemAdmin]


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, delete role (admin)."""
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsSystemAdmin]
