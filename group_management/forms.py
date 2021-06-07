from typing import List, Tuple

from wtforms import TextAreaField, IntegerField, StringField, BooleanField, SubmitField, SelectField

from CTFd.forms import BaseForm
from CTFd.forms.setup import SetupForm


class USetupForm(SetupForm):
    ctf_groups = TextAreaField(
        "Event Groups", description="Groups which take part in the event"
    )


class GroupModifyForm(BaseForm):
    group_id = IntegerField()
    action = StringField()


class GroupCreateForm(BaseForm):
    group_name = StringField("Group Name")
    active = BooleanField("Active")
    submit = SubmitField("Create")


class GroupEditForm(BaseForm):
    group_name = StringField("New Name")
    submit = SubmitField("Edit")


class GroupDeleteForm(BaseForm):
    delete = BooleanField("Delete group?")
    submit = SubmitField("Edit")


class GroupRemoveTeamForm(BaseForm):
    team_id = StringField("Team ID")
    submit = SubmitField("Remove")


class ImportStudentsForm(BaseForm):
    student_info = TextAreaField(
        "Students Info", description="Paste students info"
    )
    submit = SubmitField("Import")

