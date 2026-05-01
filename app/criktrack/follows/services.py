from __future__ import annotations

from flask_login import current_user

from ..models import Follow, FollowTarget


def followed_ids(target_type: FollowTarget) -> set[int]:
    """Return the set of target ids the current user follows for a given type."""
    if not current_user.is_authenticated:
        return set()
    rows = (
        Follow.query.with_entities(Follow.target_id)
        .filter_by(user_id=current_user.id, target_type=target_type)
        .all()
    )
    return {row[0] for row in rows}


def is_following(target_type: FollowTarget, target_id: int) -> bool:
    if not current_user.is_authenticated:
        return False
    return (
        Follow.query.filter_by(
            user_id=current_user.id,
            target_type=target_type,
            target_id=target_id,
        ).first()
        is not None
    )
