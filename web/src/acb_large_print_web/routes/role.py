"""User role management and admin promotion workflows.

This module provides routes for:
- Requesting admin promotion (POST /user/request-promotion)
- Viewing pending promotion requests (GET /admin/promotions)
- Approving/rejecting promotions (POST /admin/promotions/<user_id>/approve|reject)
- Listing all users and their roles (GET /admin/users) -- admin only
- Directly elevating users (POST /admin/users/<user_id>/promote) -- super_admin only

Promotion workflow:
1. Regular user requests promotion via /user/request-promotion
2. Admin reviews pending requests at /admin/promotions
3. Admin approves or rejects via POST endpoint
4. User's role is updated and they receive notification
"""

from __future__ import annotations

from flask import Blueprint, abort, current_app, jsonify, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user

from ..db import db
from ..models import User, UserRole
from ..permissions import require_admin, require_role
from ..email import email_configured, send_email

role_bp = Blueprint("role", __name__)


# ============================================================================
# END-USER PROMOTION REQUESTS
# ============================================================================

@role_bp.route("/user/request-promotion", methods=["GET", "POST"])
@login_required
def request_promotion():
    """Request admin promotion. GET shows form; POST submits request."""
    if current_user.role != UserRole.USER.value:
        return redirect(url_for("account.account_settings"))

    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        if not reason or len(reason) < 10:
            return render_template(
                "user/request_promotion.html",
                error="Reason must be at least 10 characters"
            )

        # Check if already has pending request
        if current_user.promotion_request_status == "pending":
            return render_template(
                "user/request_promotion.html",
                info="You already have a pending promotion request"
            )

        try:
            current_user.request_promotion(reason)
            db.session.commit()

            # Notify admins
            admins = User.query.filter(
                User.role.in_([UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value])
            ).all()

            for admin in admins:
                if email_configured():
                    send_email(
                        to=admin.email,
                        subject=f"New Admin Promotion Request from {current_user.email}",
                        html=render_template(
                            "emails/promotion_request_notification.html",
                            requester=current_user,
                            admin=admin,
                            approve_url=url_for(
                                "role.admin_approve_promotion",
                                user_id=current_user.id,
                                _external=True
                            ),
                            review_url=url_for(
                                "role.admin_promotions",
                                _external=True
                            )
                        )
                    )

            return render_template(
                "user/request_promotion.html",
                success="Promotion request submitted. Admins will review it soon."
            )
        except ValueError as e:
            return render_template(
                "user/request_promotion.html",
                error=str(e)
            )

    return render_template("user/request_promotion.html")


# ============================================================================
# ADMIN PROMOTION MANAGEMENT
# ============================================================================

@role_bp.route("/admin/promotions", methods=["GET"])
@login_required
@require_admin
def admin_promotions():
    """List all pending promotion requests. Admin only."""
    pending = User.query.filter_by(
        promotion_request_status="pending"
    ).all()

    return render_template(
        "admin/promotions.html",
        pending_requests=pending
    )


@role_bp.route("/admin/promotions/<int:user_id>/approve", methods=["POST"])
@login_required
@require_admin
def admin_approve_promotion(user_id: int):
    """Approve a promotion request. Admin only."""
    target_user = User.query.get_or_404(user_id)

    if target_user.promotion_request_status != "pending":
        return jsonify({"error": "No pending request"}), 400

    new_role = request.form.get("new_role", UserRole.ADMIN.value).strip()
    if new_role not in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value):
        return jsonify({"error": "Invalid role"}), 400

    # Only super_admin can elevate to super_admin
    if (new_role == UserRole.SUPER_ADMIN.value and 
        current_user.role != UserRole.SUPER_ADMIN.value):
        return jsonify({"error": "Only super_admin can elevate to super_admin"}), 403

    try:
        target_user.approve_promotion(current_user, new_role)
        db.session.commit()

        # Notify user
        if email_configured():
            send_email(
                to=target_user.email,
                subject="Admin Promotion Approved",
                html=render_template(
                    "emails/promotion_approved.html",
                    user=target_user,
                    approved_by=current_user,
                    new_role=new_role
                )
            )

        current_app.logger.info(
            f"User {current_user.email} approved promotion for {target_user.email} "
            f"to role {new_role}"
        )

        return jsonify({"success": True, "new_role": new_role}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@role_bp.route("/admin/promotions/<int:user_id>/reject", methods=["POST"])
@login_required
@require_admin
def admin_reject_promotion(user_id: int):
    """Reject a promotion request. Admin only."""
    target_user = User.query.get_or_404(user_id)

    if target_user.promotion_request_status != "pending":
        return jsonify({"error": "No pending request"}), 400

    rejection_reason = request.form.get("reason", "").strip()

    try:
        target_user.reject_promotion(current_user)
        db.session.commit()

        # Notify user
        if email_configured():
            send_email(
                to=target_user.email,
                subject="Admin Promotion Request Declined",
                html=render_template(
                    "emails/promotion_rejected.html",
                    user=target_user,
                    rejected_by=current_user,
                    reason=rejection_reason
                )
            )

        current_app.logger.info(
            f"User {current_user.email} rejected promotion for {target_user.email}"
        )

        return jsonify({"success": True}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ============================================================================
# ADMIN USER MANAGEMENT
# ============================================================================

@role_bp.route("/admin/users", methods=["GET"])
@login_required
@require_admin
def admin_users():
    """List all users and their roles. Admin only."""
    users = User.query.order_by(User.role.desc(), User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@role_bp.route("/admin/users/<int:user_id>/promote", methods=["POST"])
@login_required
@require_role(UserRole.SUPER_ADMIN)
def admin_direct_promote(user_id: int):
    """Directly promote a user to admin/super_admin. Super admin only."""
    target_user = User.query.get_or_404(user_id)
    
    if target_user.id == current_user.id:
        return jsonify({"error": "Cannot change own role"}), 400

    new_role = request.form.get("new_role", UserRole.ADMIN.value).strip()
    if new_role not in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value):
        return jsonify({"error": "Invalid role"}), 400

    old_role = target_user.role
    target_user.role = new_role

    db.session.commit()

    # Notify user
    if email_configured():
        send_email(
            to=target_user.email,
            subject="Your Role Has Been Updated",
            html=render_template(
                "emails/role_updated.html",
                user=target_user,
                old_role=old_role,
                new_role=new_role,
                updated_by=current_user
            )
        )

    current_app.logger.info(
        f"User {current_user.email} promoted {target_user.email} "
        f"from {old_role} to {new_role}"
    )

    return jsonify({"success": True, "new_role": new_role}), 200


@role_bp.route("/admin/users/<int:user_id>/demote", methods=["POST"])
@login_required
@require_role(UserRole.SUPER_ADMIN)
def admin_demote_user(user_id: int):
    """Demote a user to a lower role. Super admin only."""
    target_user = User.query.get_or_404(user_id)
    
    if target_user.id == current_user.id:
        return jsonify({"error": "Cannot change own role"}), 400

    new_role = request.form.get("new_role", UserRole.USER.value).strip()
    if new_role not in (UserRole.USER.value, UserRole.ADMIN.value):
        return jsonify({"error": "Invalid role"}), 400

    old_role = target_user.role
    target_user.role = new_role
    # Clear promotion workflow state on demotion
    target_user.promotion_request_status = None
    target_user.promotion_request_reason = None

    db.session.commit()

    # Notify user
    if email_configured():
        send_email(
            to=target_user.email,
            subject="Your Role Has Been Updated",
            html=render_template(
                "emails/role_updated.html",
                user=target_user,
                old_role=old_role,
                new_role=new_role,
                updated_by=current_user
            )
        )

    current_app.logger.info(
        f"User {current_user.email} demoted {target_user.email} "
        f"from {old_role} to {new_role}"
    )

    return jsonify({"success": True, "new_role": new_role}), 200
