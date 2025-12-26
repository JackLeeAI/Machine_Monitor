from utils.db import db

class Workshop(db.Model):
    __tablename__ = 'Dev_Place'
    __bind_key__ = 'dev'

    ID = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(30), nullable=False, unique=True)

    # 关联设备
    equipments = db.relationship('Equipment', backref='workshop', lazy=True, foreign_keys='Equipment.Pos_ID')

    def to_dict(self):
        return {'id': self.ID, 'name': self.name}