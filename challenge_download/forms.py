from wtforms import IntegerField, StringField, FileField
from CTFd.forms import BaseForm


class ChallengeDownloadForm(BaseForm):
    challenge_id = IntegerField()
    action = StringField()


class ChallengeUploadForm(BaseForm):
    challenge_zips = FileField()
