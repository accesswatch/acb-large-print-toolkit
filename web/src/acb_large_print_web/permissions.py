"""Role-based access control (RBAC) and permission enforcement.

This module provides decorators and helpers for checking user roles before
allowing access to protected routes and functions. It integrates with Flask-Login
and the User model's role hierarchy.

Role hierarchy (least to most privileged):
- USER (1): Regular end-user
- ADMIN (2): System administrator
- SUPER_ADMIN (3): Super administrator (unrestricted)

Example usage:

    from flask import Blueprint
    from .permissions import require_role, require_admin

    bp = Blueprint('admin', __name__)

    @bp.route('/admin/dashboard')
    @require_admin
    def admin_dashboard():
        return render_template('admin/dashboard.html')

    @bp.route('/admin/super/config')
    @require_role('super_admin')
    def super_admin_config():
        return render_template('admin/config.html')
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, TypeVar

from flask import abort, current_app
from flask_login import current_user

from .models import UserRole

F = TypeVar("F", bound=Callable)


def require_role(required_role: str | UserRole) -> Callable[[F], F]:
    """Decorator: enforce minimum role requirement.
    
    If the current user doesn't have the required role or higher, abort(403).
    
    Args:
        required_role: Role name as string ('user', 'admin', 'super_admin')
                      or UserRole enum value.
    
    Returns:
        Decorated function that checks user role before executing.
    
    Example:
        @app.route('/admin')
        @require_role('admin')
        def admin_page():
            return "Admin area"
    """
    if isinstance(required_role, UserRole):
        required = required_role.value
    else:
        required = required_role

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)  # Unauthorized
            if not current_user.has_role(required):
                current_app.logger.warning(
                    f"User {current_user.email} (role={current_user.role}) "
                    f"attempted access to {required}-protected route"
                )
                abort(403)  # Forbidden
            return func(*args, **kwargs)
        return wrapped  # type: ignore
    return decorator


def require_admin(func: F) -> F:
    """Decorator: enforce admin or higher role.
    
    Shorthand for @require_role('admin'). Aborts with 403 if user is not admin.
    
    Example:
        @app.route('/admin/users')
        @require_admin
        def admin_users():
            return "User management"
    """
    return require_role(UserRole.ADMIN.value)(func)


def require_super_admin(func: F) -> F:
    """Decorator: enforce super_admin role only.
    
    Shorthand for @require_role('super_admin'). Aborts with 403 if user is not super_admin.
    
    Example:
        @app.route('/admin/danger/delete-db')
        @require_super_admin
        def danger_delete_db():
            return "Dangerous operation"
    """
    return require_role(UserRole.SUPER_ADMIN.value)(func)


def is_current_user_admin() -> bool:
    """Check if current user is admin or super_admin without raising exception.
    
    Useful for conditional template rendering or logic branches.
    
    Returns:
        True if user is authenticated and has admin+ role; False otherwise.
    """
    return current_user.is_authenticated and current_user.is_admin()


def is_current_user_super_admin() -> bool:
    """Check if current user is super_admin without raising exception.
    
    Useful for conditional template rendering or logic branches.
    
    Returns:
        True if user is authenticated and has super_admin role; False otherwise.
    """
    return current_user.is_authenticated and current_user.is_super_admin()


def can_user_manage_roles(target_user_id: int) -> bool:
    """Check if current user can manage (approve/reject) promotions for a target user.
    
    Admin+ can approve promotions for regular users to admin role.
    Only super_admin can promote users to super_admin.
    
    Args:
        target_user_id: ID of the user being managed
    
    Returns:
        True if current user can manage the target user's role; False otherwise.
    """
    if not current_user.is_authenticated:
        return False
    if not current_user.is_admin():
        return False
    # Admins can manage regular users; super_admins can manage anyone
    if current_user.is_super_admin():
        return True
    # Regular admins cannot manage other admins or super_admins
    if target_user_id == current_user.id:
        return False  # Cannot manage own role
    return True
