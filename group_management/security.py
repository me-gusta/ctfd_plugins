from flask import url_for, redirect, abort, request, render_template

from CTFd.plugins.group_management.util import get_current_group
from CTFd.utils.user import get_current_team, is_admin


def check_group_decorator(func):
    """ Checks if user has a group and if group is active. Only for non-API routes """

    def wrapper(*args, **kwargs):
        current_team = get_current_team()
        if not current_team:
            return redirect(url_for("teams.private", next=request.full_path))
        current_group = get_current_group(current_team)
        if not is_admin():
            if not current_group:
                return redirect(url_for('groups_choice', next=request.full_path))
            if not current_group.active:
                return (
                    render_template(
                        "errors/403.html",
                        error="Your group is inactive. Ask your teacher for access permission",
                    ),
                    403,
                )
        return func(*args, **kwargs)

    return wrapper


def check_group_api_decorator(func):
    """ Checks if user has a group and if group is active. Only for API routes  """

    def wrapper(*args, **kwargs):
        current_group = get_current_group(get_current_team())
        if not is_admin():
            if not current_group:
                return redirect(url_for('groups_choice'))
            if not current_group.active:
                return abort(403)
        return func(*args, **kwargs)

    return wrapper
