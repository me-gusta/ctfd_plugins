from flask import current_app as app
from flask import redirect, render_template, request, url_for
from flask import session
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import abort

from CTFd.cache import cache
from CTFd.constants.config import (
    AccountVisibilityTypes,
    ConfigTypes,
    RegistrationVisibilityTypes,
    ScoreVisibilityTypes,
)
from CTFd.constants.config import ChallengeVisibilityTypes
from CTFd.constants.themes import DEFAULT_THEME
from CTFd.models import (
    Admins,
    Pages,
    Users,
    db, Teams,
)
from CTFd.plugins.group_management.forms import USetupForm, GroupModifyForm, GroupCreateForm, GroupEditForm, \
    GroupDeleteForm, GroupRemoveTeamForm, ImportStudentsForm
from CTFd.plugins.group_management.models import Groups
from CTFd.plugins.group_management.util import get_current_group
from CTFd.utils import config, get_config, set_config
from CTFd.utils import validators
from CTFd.utils.decorators import admins_only
from CTFd.utils.email import (
    DEFAULT_PASSWORD_RESET_BODY,
    DEFAULT_PASSWORD_RESET_SUBJECT,
    DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY,
    DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT,
    DEFAULT_USER_CREATION_EMAIL_BODY,
    DEFAULT_USER_CREATION_EMAIL_SUBJECT,
    DEFAULT_VERIFICATION_EMAIL_BODY,
    DEFAULT_VERIFICATION_EMAIL_SUBJECT,
)
from CTFd.utils.helpers import get_errors
from CTFd.utils.modes import USERS_MODE
from CTFd.utils.security.auth import login_user
from CTFd.utils.security.csrf import generate_nonce
from CTFd.utils.security.signing import (
    serialize,
)
from CTFd.utils.uploads import upload_file
from CTFd.utils.user import get_current_team


def setup():
    errors = get_errors()
    if not config.is_setup():
        if not session.get("nonce"):
            session["nonce"] = generate_nonce()
        if request.method == "POST":
            # General
            ctf_name = request.form.get("ctf_name")
            ctf_description = request.form.get("ctf_description")
            user_mode = request.form.get("user_mode", USERS_MODE)
            set_config("ctf_name", ctf_name)
            set_config("ctf_description", ctf_description)
            set_config("user_mode", user_mode)

            # Style
            ctf_logo = request.files.get("ctf_logo")
            if ctf_logo:
                f = upload_file(file=ctf_logo)
                set_config("ctf_logo", f.location)

            ctf_small_icon = request.files.get("ctf_small_icon")
            if ctf_small_icon:
                f = upload_file(file=ctf_small_icon)
                set_config("ctf_small_icon", f.location)

            theme = request.form.get("ctf_theme", DEFAULT_THEME)
            set_config("ctf_theme", theme)
            theme_color = request.form.get("theme_color")
            theme_header = get_config("theme_header")
            if theme_color and bool(theme_header) is False:
                # Uses {{ and }} to insert curly braces while using the format method
                css = (
                    '<style id="theme-color">\n'
                    ":root {{--theme-color: {theme_color};}}\n"
                    ".navbar{{background-color: var(--theme-color) !important;}}\n"
                    ".jumbotron{{background-color: var(--theme-color) !important;}}\n"
                    "</style>\n"
                ).format(theme_color=theme_color)
                set_config("theme_header", css)

            # DateTime
            start = request.form.get("start")
            end = request.form.get("end")
            set_config("start", start)
            set_config("end", end)
            set_config("freeze", None)

            # Administration
            name = request.form["name"]
            email = request.form["email"]
            password = request.form["password"]

            name_len = len(name) == 0
            names = Users.query.add_columns("name", "id").filter_by(name=name).first()
            emails = (
                Users.query.add_columns("email", "id").filter_by(email=email).first()
            )
            pass_short = len(password) == 0
            pass_long = len(password) > 128
            valid_email = validators.validate_email(request.form["email"])
            team_name_email_check = validators.validate_email(name)

            if not valid_email:
                errors.append("Please enter a valid email address")
            if names:
                errors.append("That user name is already taken")
            if team_name_email_check is True:
                errors.append("Your user name cannot be an email address")
            if emails:
                errors.append("That email has already been used")
            if pass_short:
                errors.append("Pick a longer password")
            if pass_long:
                errors.append("Pick a shorter password")
            if name_len:
                errors.append("Pick a longer user name")

            if len(errors) > 0:
                return render_template(
                    "setup.html",
                    errors=errors,
                    name=name,
                    email=email,
                    password=password,
                    state=serialize(generate_nonce()),
                )

            admin = Admins(
                name=name, email=email, password=password, type="admin", hidden=True
            )

            # Create an empty index page
            page = Pages(title=None, route="index", content="", draft=False)

            # Upload banner
            default_ctf_banner_location = url_for("views.themes", path="img/logo.png")
            ctf_banner = request.files.get("ctf_banner")
            if ctf_banner:
                f = upload_file(file=ctf_banner, page_id=page.id)
                default_ctf_banner_location = url_for("views.files", path=f.location)

            # Splice in our banner
            index = f"""<div class="row">
    <div class="col-md-6 offset-md-3">
        <img class="w-100 mx-auto d-block" style="max-width: 500px;padding: 50px;padding-top: 14vh;" src="{default_ctf_banner_location}" />
        <h3 class="text-center">
            <p>A cool CTF platform from <a href="https://ctfd.io">ctfd.io</a></p>
            <p>Follow us on social media:</p>
            <a href="https://twitter.com/ctfdio"><i class="fab fa-twitter fa-2x" aria-hidden="true"></i></a>&nbsp;
            <a href="https://facebook.com/ctfdio"><i class="fab fa-facebook fa-2x" aria-hidden="true"></i></a>&nbsp;
            <a href="https://github.com/ctfd"><i class="fab fa-github fa-2x" aria-hidden="true"></i></a>
        </h3>
        <br>
        <h4 class="text-center">
            <a href="admin">Click here</a> to login and setup your CTF
        </h4>
    </div>
</div>"""
            page.content = index

            # Visibility
            set_config(
                ConfigTypes.CHALLENGE_VISIBILITY, ChallengeVisibilityTypes.PRIVATE
            )
            set_config(
                ConfigTypes.REGISTRATION_VISIBILITY, RegistrationVisibilityTypes.PUBLIC
            )
            set_config(ConfigTypes.SCORE_VISIBILITY, ScoreVisibilityTypes.PUBLIC)
            set_config(ConfigTypes.ACCOUNT_VISIBILITY, AccountVisibilityTypes.PUBLIC)

            # Verify emails
            set_config("verify_emails", None)

            set_config("mail_server", None)
            set_config("mail_port", None)
            set_config("mail_tls", None)
            set_config("mail_ssl", None)
            set_config("mail_username", None)
            set_config("mail_password", None)
            set_config("mail_useauth", None)

            # Set up default emails
            set_config("verification_email_subject", DEFAULT_VERIFICATION_EMAIL_SUBJECT)
            set_config("verification_email_body", DEFAULT_VERIFICATION_EMAIL_BODY)

            set_config(
                "successful_registration_email_subject",
                DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_SUBJECT,
            )
            set_config(
                "successful_registration_email_body",
                DEFAULT_SUCCESSFUL_REGISTRATION_EMAIL_BODY,
            )

            set_config(
                "user_creation_email_subject", DEFAULT_USER_CREATION_EMAIL_SUBJECT
            )
            set_config("user_creation_email_body", DEFAULT_USER_CREATION_EMAIL_BODY)

            set_config("password_reset_subject", DEFAULT_PASSWORD_RESET_SUBJECT)
            set_config("password_reset_body", DEFAULT_PASSWORD_RESET_BODY)

            set_config(
                "password_change_alert_subject",
                "Password Change Confirmation for {ctf_name}",
            )
            set_config(
                "password_change_alert_body",
                (
                    "Your password for {ctf_name} has been changed.\n\n"
                    "If you didn't request a password change you can reset your password here: {url}"
                ),
            )

            set_config("setup", True)

            # Groups
            ctf_groups_raw = request.form.get("ctf_groups")
            ctf_groups = {x for x in ctf_groups_raw.split('\n') if x}
            for ctf_group in ctf_groups:
                group = Groups(name=ctf_group)
                db.session.add(group)
            db.session.commit()

            try:
                db.session.add(admin)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

            try:
                db.session.add(page)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

            login_user(admin)

            db.session.close()
            with app.app_context():
                cache.clear()

            return redirect(url_for("views.static_html"))
        return render_template("setup.html", state=serialize(generate_nonce()), form=USetupForm())
    return redirect(url_for("views.static_html"))


@admins_only
def admin_groups():
    if request.method == 'POST':
        try:
            group_id = int(request.form['group_id'])
            action = request.form['action']
        except (KeyError, AttributeError, TypeError):
            return abort(400)

        group = Groups.query.get(group_id)

        if not group:
            return abort(404)

        if action == 'toggle':
            group.active = not group.active
        elif action == 'set_only_active':
            for g in Groups.query.all():
                g.active = False
            group.active = True
        elif action == 'set_all_active':
            for g in Groups.query.all():
                g.active = True
        elif action == 'set_all_inactive':
            for g in Groups.query.all():
                g.active = False
        else:
            return abort(404)

        db.session.commit()
        db.session.close()
        return redirect(url_for('admin_groups'))

    groups = Groups.query.all()
    form = GroupModifyForm()
    return render_template('admin_groups.html', groups=groups, form=form)


@admins_only
def admin_create_group():
    if request.method == 'POST':
        group_name = request.form.get("group_name")
        active = request.form.get("active") is not None
        group = Groups(name=group_name, active=active)
        db.session.add(group)
        db.session.commit()
        db.session.close()
        return redirect(url_for('admin_groups'))
    form = GroupCreateForm()
    return render_template('admin_create_group.html', form=form)


@admins_only
def admin_group(group_id):
    group = Groups.query.filter_by(id=group_id).first_or_404()
    if request.method == 'POST':
        delete = request.form.get("delete") is not None
        if delete:
            db.session.delete(group)
            db.session.commit()
            db.session.close()
            return redirect(url_for('admin_groups'))
        remove_team_id_raw = request.form.get("team_id")
        if remove_team_id_raw:
            try:
                team = Teams.query.filter_by(id=int(remove_team_id_raw)).first_or_404()
            except TypeError:
                return abort(400)
            if team not in group.members:
                return abort(400)
            group.members.remove(team)
            db.session.commit()
            db.session.close()
            return redirect(url_for('admin_group', group_id=group_id))

        group_name = request.form.get("group_name")
        if group_name:
            group.name = group_name
            db.session.commit()
            db.session.close()
            return redirect(url_for('admin_group', group_id=group_id))

    group = Groups.query.get(group_id)
    teams = group.members
    members = [user for team in teams for user in team.members]
    edit_form = GroupEditForm()
    delete_form = GroupDeleteForm()
    remove_team_form = GroupRemoveTeamForm()
    return render_template('admin_group.html', group=group, teams=teams, members=members,
                           edit_form=edit_form, delete_form=delete_form, remove_team_form=remove_team_form)


@admins_only
def admin_import_students():
    if request.method == 'POST':
        student_info: str = request.form.get("student_info")
        student_info_rows = student_info.splitlines()
        students_data = [x.split() for x in student_info_rows]
        try:
            if len(students_data[0]) == 5:
                # Remove on index 3
                students_data = [x[:3] + x[-1::] for x in students_data]
        except IndexError:
            return abort(400, 'Incorrect student data.')
        if len(students_data[0]) != 4:
            return abort(400, 'Incorrect student data. Too many columns.')
        users = []
        for data in students_data:
            name = ' '.join(data[:3])
            password = data[-1]
            user = Users(name=name, password=password, email=f'{hash((name, password))}@example.com')
            db.session.add(user)
            users.append({'name': name, 'password': password})
        db.session.commit()
        db.session.close()
        return render_template('admin_import_students_list.html', users=users)

    form = ImportStudentsForm()
    return render_template('admin_import_students.html', form=form)


# @admins_only
# def admin_groups_modify():
#


def groups_choice():
    if get_current_group(get_current_team()):
        return redirect(url_for('challenges.listing'))
    groups = Groups.query.all()
    current_team = get_current_team()
    try:
        is_captain = current_team.captain_id == session["id"]
    except AttributeError:
        is_captain = False
    return render_template("groups_choice.html", groups=groups, is_captain=is_captain)


def groups_choose(group_id):
    current_team = get_current_team()
    if current_team.captain_id != session["id"] or get_current_group(current_team):
        return redirect(url_for('groups_choice'))

    group = Groups.query.filter_by(id=group_id).first_or_404()
    group.members.append(current_team)
    db.session.commit()
    db.session.close()
    return redirect(url_for('challenges.listing'))
