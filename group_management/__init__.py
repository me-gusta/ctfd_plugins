from ... import CTFdFlask

from CTFd.plugins import register_plugin_assets_directory, override_template
from CTFd.plugins.migrations import upgrade
from .security import check_group_api_decorator, check_group_decorator
from .models import Groups
from .util import get_template_path
from .views import setup, admin_groups, groups_choice, groups_choose, admin_create_group, \
    admin_group,  admin_import_students


def load(app: CTFdFlask):
    app.db.create_all()
    upgrade()
    register_plugin_assets_directory(
        app, base_path="/plugins/group_management/assets/"
    )

    # Templates Overriding
    override_template('setup.html', open(get_template_path('setup.html')).read())
    override_template('admin_groups.html', open(get_template_path('admin_groups.html')).read())

    # New Templates
    override_template('groups_choice.html', open(get_template_path('groups_choice.html')).read())
    override_template('admin_create_group.html', open(get_template_path('admin_create_group.html')).read())
    override_template('admin_group.html', open(get_template_path('admin_group.html')).read())
    override_template('admin_import_students.html', open(get_template_path('admin_import_students.html')).read())
    override_template('admin_import_students_list.html', open(get_template_path('admin_import_students_list.html')).read())

    # Routes Overriding
    app.view_functions['views.setup'] = setup

    # Decorators
    app.view_functions['challenges.listing'] = check_group_decorator(app.view_functions['challenges.listing'])

    app.view_functions['api.challenges_challenge_list'] = check_group_api_decorator(
        app.view_functions['api.challenges_challenge_list'])
    app.view_functions['api.challenges_challenge'] = check_group_api_decorator(
        app.view_functions['api.challenges_challenge'])
    app.view_functions['api.challenges_challenge_attempt'] = check_group_api_decorator(
        app.view_functions['api.challenges_challenge_attempt'])

    # New Routes
    app.add_url_rule('/groups/import', view_func=admin_import_students, methods=['GET', 'POST'])
    app.add_url_rule('/groups/choice', view_func=groups_choice)
    app.add_url_rule('/groups/choose/<group_id>', view_func=groups_choose)

    app.add_url_rule('/admin/groups', view_func=admin_groups, methods=['GET', 'POST'])
    app.add_url_rule('/admin/group/<group_id>', view_func=admin_group, methods=['GET', 'POST'])
    app.add_url_rule('/admin/groups/create', view_func=admin_create_group, methods=['GET', 'POST'])
