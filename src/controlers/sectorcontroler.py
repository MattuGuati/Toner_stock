from flask import request, flash
from models import db, Sector


def all_sectors():
    return Sector.query.all()

def one_sector(sector_id):
    return Sector.query.get(sector_id)
    
def add_sector(nombre, duracion_predefinida):
    new_sector = Sector(nombre = nombre, duracion_predefinida = duracion_predefinida)
    db.session.add(new_sector)
    db.session.commit()

def del_sector(sector_id):
    sector = Sector.query.get(sector_id)
    if sector:
        db.session.delete(sector)
        db.session.commit()
    return sector is not None

