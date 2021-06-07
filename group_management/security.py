from flask import url_for, redirect, abort, request, render_template

from CTFd.plugins.group_management.util import get_current_group
from CTFd.utils.user import get_current_team, authed, is_admin


def challenges_listing_decorator(func):
    """ Checks if user has a group and if group is active. Only for non-API routes """

    def wrapper(*args, **kwargs):
        current_team = get_current_team()
        if not current_team:
            return redirect(url_for("teams.private", next=request.full_path))
        current_group = get_current_group(current_team)
        if not current_group and not is_admin():
            return redirect(url_for('groups_choice', next=request.full_path))
        if (current_group and not current_group.active) and not is_admin():
            return (
                render_template(
                    "errors/403.html",
                    error="Your group is inactive. Ask your teacher for access permission",
                ),
                403,
            )
        return func(*args, **kwargs)

    return wrapper


def check_group_decorator(func):
    """ Checks if user has a group and if group is active. Only for API routes  """

    def wrapper(*args, **kwargs):
        current_group = get_current_group(get_current_team())
        if not current_group and not is_admin():
            return redirect(url_for('auth.login'))
        if (current_group and not current_group.active) and not is_admin():
            return abort(403)
        return func(*args, **kwargs)

    return wrapper


def check_if_group_banned():
    """ Prevent access for banned groups """
    if request.endpoint == "views.themes":
        return
    current_group = get_current_group(get_current_team())
    if authed() and (current_group and current_group.banned):
        return (
            render_template(
                "errors/403.html", error="Your group has been banned from this CTF"
            ),
            403,
        )
