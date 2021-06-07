import os


def get_template_path(template_name: str):
    template_folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'templates')
    template_path = os.path.join(template_folder_path, template_name)
    return template_path


def get_current_group(team):
    try:
        return team.groups[0]
    except (IndexError, AttributeError):
        return None
