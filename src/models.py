from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Toner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(64), unique=True, nullable=False)
    cantidad_actual = db.Column(db.Integer, nullable=False)

class Preferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    min_stock = db.Column(db.Integer, nullable=False)
    proveedor_email = db.Column(db.String(120), nullable=False)
    toner_id = db.Column(db.Integer, db.ForeignKey('toner.id'), nullable=False)
    toner = db.relationship('Toner', backref=db.backref('preferences', uselist=False))

class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(64), unique=True, nullable=False)
    duracion_predefinida = db.Column(db.Integer, nullable=False)

class Movement(db.Model):
    #agregar fecha-hora
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(10), nullable=False)  # 'Entrada' or 'Salida'
    cantidad = db.Column(db.Integer, nullable=False)
    toner_id = db.Column(db.Integer, db.ForeignKey('toner.id'), nullable=False)
    toner = db.relationship('Toner', backref=db.backref('movements', lazy=True))
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=False)
    sector = db.relationship('Sector', backref=db.backref('movements', lazy=True))
    reverted = db.Column(db.Boolean, default=False, nullable=False)
