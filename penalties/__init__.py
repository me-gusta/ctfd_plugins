from flask import Blueprint

from CTFd.models import Challenges, db
from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.schemas.awards import AwardSchema


class PenaltyChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "penalty"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    is_active = db.Column(db.Boolean, default=False)
    penalty_amount = db.Column(db.Integer)

    def __init__(self, *args, **kwargs):
        super(PenaltyChallenge, self).__init__(**kwargs)


class PenaltyCTFChallenge(BaseChallenge):
    id = "penalty"
    name = "penalty"
    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        "create": "/plugins/penalties/assets/create.html",
        "update": "/plugins/penalties/assets/update.html",
        "view": "/plugins/penalties/assets/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/penalties/assets/create.js",
        "update": "/plugins/penalties/assets/update.js",
        "view": "/plugins/penalties/assets/view.js",
    }
    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/penalties/assets/"
    # Blueprint used to access the static_folder directory.
    blueprint = Blueprint(
        "penalties",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = PenaltyChallenge

    @classmethod
    def create(cls, request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        data = request.form or request.get_json()
        data['is_active'] = bool(int(data['is_active']))
        data['penalty_amount'] = max(0, min(100, int(data['penalty_amount'])))
        challenge = cls.challenge_model(**data)

        db.session.add(challenge)
        db.session.commit()

        return challenge

    @classmethod
    def read(cls, challenge):
        """
        This method is in used to access the data of a challenge in a format processable by the front end.

        :param challenge:
        :return: Challenge object, data dictionary to be returned to the user
        """
        challenge = PenaltyChallenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id,
            "name": challenge.name,
            "value": challenge.value,
            "penalty_amount": challenge.penalty_amount,
            "is_active": challenge.is_active,
            "description": challenge.description,
            "category": challenge.category,
            "state": challenge.state,
            "max_attempts": challenge.max_attempts,
            "type": challenge.type,
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

    @classmethod
    def update(cls, challenge, request):
        """
        This method is used to update the information associated with a challenge. This should be kept strictly to the
        Challenges table and any child tables.

        :param challenge:
        :param request:
        :return:
        """
        data = request.form or request.get_json()
        for attr, value in data.items():
            if attr in ('is_active',) and value.isdigit():
                value = bool(int(value))
            setattr(challenge, attr, value)
        db.session.commit()
        return challenge

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)
        if challenge.is_active:
            schema = AwardSchema()
            req = {
                'user_id': team.captain_id,
                'team_id': team.id,
                'value': int(-(challenge.value/100) * challenge.penalty_amount),
                'name': f'Penalty for Task#{challenge.name}'
            }
            response = schema.load(req, session=db.session)
            db.session.add(response.data)
            db.session.commit()


def load(app):
    app.db.create_all()
    # upgrade()
    CHALLENGE_CLASSES["penalty"] = PenaltyCTFChallenge
    register_plugin_assets_directory(
        app, base_path="/plugins/penalties/assets/"
    )
