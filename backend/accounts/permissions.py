"""
Role-based access control. Admin can add/remove/modify roles without code change;
permission checks use role names from the spec.
"""
from rest_framework import permissions


class IsSystemAdmin(permissions.BasePermission):
    """Only System Administrator."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('System Administrator')


class IsPoliceChief(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('Police Chief')


class IsCaptain(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('Captain')


class IsSergeant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('Sergeant')


class IsDetective(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('Detective')


class IsPoliceOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('Police Officer')


class IsIntern(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('Intern')


class IsJudge(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('Judge')


class IsForensicDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.has_role('Forensic Doctor')


def has_any_role(user, role_names):
    """Check if user has at least one of the given roles."""
    if not user.is_authenticated:
        return False
    return any(user.has_role(name) for name in role_names)


class IsSupervisor(permissions.BasePermission):
    """Sergeant or above (Captain, Chief)."""
    def has_permission(self, request, view):
        return has_any_role(
            request.user,
            ['Sergeant', 'Captain', 'Police Chief', 'System Administrator'],
        )


class IsOfficerOrAbove(permissions.BasePermission):
    """Police Officer, Detective, Sergeant, Captain, Chief, Admin."""
    def has_permission(self, request, view):
        return has_any_role(
            request.user,
            [
                'Police Officer', 'Detective', 'Sergeant', 'Captain',
                'Police Chief', 'System Administrator',
            ],
        )


class IsTraineeOrAbove(permissions.BasePermission):
    """Intern (trainee) or any officer."""
    def has_permission(self, request, view):
        return has_any_role(
            request.user,
            [
                'Intern', 'Police Officer', 'Detective', 'Sergeant', 'Captain',
                'Police Chief', 'System Administrator',
            ],
        )


class CanReferCaseToJudiciary(permissions.BasePermission):
    """Captain, Police Chief, or Judge can refer case / create trial."""
    def has_permission(self, request, view):
        return has_any_role(
            request.user,
            ['Captain', 'Police Chief', 'Judge', 'System Administrator'],
        )
