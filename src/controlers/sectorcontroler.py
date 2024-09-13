from flask import request, flash
from models import db, Sector


def all_sectors():
    return Sector.query.all()

def one_sector(sector_id):
    if isinstance(sector_id, str):
        return Sector.query.filter_by(nombre = sector_id).first()
    else: 
        return Sector.query.get(sector_id)
    
def add_sector(nombre = str, duracion_predefinida = int):
    new_sector = Sector(nombre = nombre, duracion_predefinida = duracion_predefinida)
    db.session.add(new_sector)
    db.session.commit()

def del_sector(sector_id):
    sector = one_sector(sector_id) 
    db.session.delete(sector)
    db.session.commit()
