from flask import request, flash
from models import db, Movement
from datetime import datetime
from sqlalchemy import desc
from .tonercontroler import one_toner

def all_movements():
    return Movement.query.order_by(desc(Movement.fecha)).all()

def one_movement(movement_id):
    return Movement.query.get(movement_id)
    
def new_movement(tipo, cantidad, toner_id, sector_id):
    new_movement = Movement(
        fecha = datetime.now(),
        tipo = tipo, 
        cantidad = cantidad, 
        toner_id = toner_id, 
        sector_id = sector_id)
    
    toner = one_toner(new_movement.toner_id)
    toner.cantidad_actual -= new_movement.cantidad

    db.session.add(new_movement)
    db.session.commit()

def del_movement(movement_id):
    movement = Movement.query.get(movement_id)
    if movement:
        db.session.delete(movement)
        db.session.commit()
    return movement is not None


def rev_movement(movement_id):
    movimiento = one_movement(movement_id)
    if movimiento:
        toner = one_toner(movimiento.toner_id)
        if movimiento.tipo == 'Salida':
            toner.cantidad_actual += movimiento.cantidad
        elif movimiento.tipo == 'Entrada':
            toner.cantidad_actual -= movimiento.cantidad

        movimiento.reverted = True
        db.session.commit()
        
        flash('Movimiento revertido con éxito', 'success')
    else:
        flash('Movimiento no encontrado', 'error')
