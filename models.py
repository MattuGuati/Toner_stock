from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Toner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(50), unique=True, nullable=False)
    cantidad_actual = db.Column(db.Integer, nullable=False)

class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    duracion_predefinida = db.Column(db.Integer, nullable=False)

class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    toner_id = db.Column(db.Integer, db.ForeignKey('toner.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=False)
    nota = db.Column(db.String(200))
