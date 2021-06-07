from CTFd.models import db

association_table = db.Table('association', db.metadata,
                             db.Column('team_id', db.Integer, db.ForeignKey('teams.id'), unique=True),
                             db.Column('group_id', db.Integer, db.ForeignKey('groups.id')))


class Groups(db.Model):
    __tablename__ = "groups"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    members = db.relationship("Teams", secondary=association_table, backref='groups')
    active = db.Column(db.Boolean, default=False)
