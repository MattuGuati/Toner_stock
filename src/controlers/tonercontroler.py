from flask import request, flash
from models import db, Toner


def all_toners():
    return Toner.query.all()

def one_toner(toner_id):
    return Toner.query.get(toner_id)
    
def add_toner(modelo, cantidad_actual):
    new_toner = Toner(modelo = modelo, cantidad_actual = cantidad_actual)
    db.session.add(new_toner)
    db.session.commit()

def plus_toner(toner_id, cantidad):
    toner = Toner.query.get(toner_id)
    toner.cantidad_actual = toner.cantidad_actual + cantidad
    db.session.commit()

def del_toner(toner_id):
    toner = Toner.query.get(toner_id)
    if toner:
        db.session.delete(toner)
        db.session.commit()
    return toner is not None

