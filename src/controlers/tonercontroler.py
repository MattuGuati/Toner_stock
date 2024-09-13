from flask import request, flash
from models import db, Toner, Sector


def all_toners():
    return Toner.query.all()

def one_toner(toner_id):
    return Toner.query.get(toner_id)
    
def add_toner(modelo, cantidad_actual):
    new_toner = Toner(modelo = modelo, cantidad_actual = cantidad_actual)
    db.session.add(new_toner)
    db.session.commit()

def less_toner(toner_id, cantidad):
    toner = one_toner(toner_id)
    try:
        toner.cantidad_actual = toner.cantidad_actual - cantidad
        db.session.commit()
        flash('Movimiento registrado exitosamente', 'success')
        return False
    except ValueError as e:
        flash(str(e), 'error')
        return True

def plus_toner(toner_id, cantidad):    
    toner = one_toner(toner_id)
    
    if cantidad <= 0:
        flash('cantidad erronea', 'error')
        return True
    
    if toner_id and cantidad is not None:
            try:
                toner.cantidad_actual = toner.cantidad_actual + cantidad
                db.session.commit()
                flash('Movimiento registrado exitosamente', 'success')
                return False
            except ValueError as e:
                flash(str(e), 'error')
                return True
    else:
        flash('Faltan datos en el formulario', 'error')
        return True


def del_toner(toner_id):
    toner = one_toner(toner_id)
    if toner:
        db.session.delete(toner)
        db.session.commit()
    return toner is not None

