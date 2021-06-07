from CTFd.plugins import register_plugin_assets_directory, override_template
from CTFd.plugins.migrations import upgrade
from .security import check_group_decorator, check_if_group_banned, challenges_listing_decorator
from .models import Groups
from .util import get_template_path
from .views import setup, admin_groups, groups_choice, groups_choose, admin_groups_modify, admin_create_group, \
    admin_group,  admin_import_students


def load(app):
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
    # for k, v in app.view_functions.items():
    #     print(f'{k}: {v}')
    app.view_functions['views.setup'] = setup

    # Middleware
    app.view_functions['challenges.listing'] = challenges_listing_decorator(app.view_functions['challenges.listing'])

    app.view_functions['api.challenges_challenge_list'] = check_group_decorator(
        app.view_functions['api.challenges_challenge_list'])
    app.view_functions['api.challenges_challenge'] = check_group_decorator(
        app.view_functions['api.challenges_challenge'])
    app.view_functions['api.challenges_challenge_attempt'] = check_group_decorator(
        app.view_functions['api.challenges_challenge_attempt'])

    app.before_request(check_if_group_banned)

    # New Routs
    app.route('/groups/import', methods=['GET', 'POST'])(admin_import_students)
    app.route('/groups/choice')(groups_choice)
    app.route('/groups/choose/<group_id>')(groups_choose)

    app.route('/admin/groups')(admin_groups)
    app.route('/admin/group/<group_id>', methods=['GET', 'POST'])(admin_group)
    app.route('/admin/groups/create', methods=['GET', 'POST'])(admin_create_group)
    app.route('/admin/groups/modify', methods=['POST'])(admin_groups_modify)
