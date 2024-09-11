from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
import pandas as pd  # Asegúrate de importar pandas
from models import db, Toner, Movement, Sector, Preferences

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

@app.route('/')
def index():
    toners = Toner.query.all()
    sectors = Sector.query.all()
    return render_template('index.html', toners=toners, sectors=sectors)

@app.route('/add_movement', methods=['POST'])
def add_movement():
    toner_id = request.form.get('toner_id')
    sector_id = request.form.get('sector_id')
    cantidad = request.form.get('cantidad', type=int)
    
    toner = Toner.query.get(toner_id)
    if not toner or not sector_id:
        flash('El tóner o sector no existe', 'error')
        return redirect(url_for('index'))
    
    if cantidad > toner.cantidad_actual:
        flash('No hay suficiente stock para realizar esta salida', 'error')
        return redirect(url_for('index'))
    
    nuevo_movimiento = Movement(toner_id=toner_id, tipo='Salida', cantidad=cantidad, sector_id=sector_id)
    toner.cantidad_actual -= cantidad
    
    db.session.add(nuevo_movimiento)
    db.session.commit()
    
    flash('Movimiento registrado con éxito', 'success')
    return redirect(url_for('index'))

@app.route('/add_pedido', methods=['POST'])
def add_pedido():
    # Lógica para añadir un pedido
    pass

@app.route('/solicitar_insumos', methods=['GET', 'POST'])
def solicitar_insumos():
    if request.method == 'POST':
        toner_ids = request.form.getlist('toners')
        pedidos = {}

        for toner_id in toner_ids:
            toner = Toner.query.get(toner_id)
            if toner.preferences.proveedor_email in pedidos:
                pedidos[toner.preferences.proveedor_email].append(toner)
            else:
                pedidos[toner.preferences.proveedor_email] = [toner]

        for proveedor_email, toners in pedidos.items():
            enviar_correo_pedido(proveedor_email, toners)

        flash('Solicitud de insumos enviada con éxito', 'success')
        return redirect(url_for('index'))

    toners = Toner.query.all()
    return render_template('solicitar_insumos.html', toners=toners)

def enviar_correo_pedido(proveedor_email, toners):
    msg = Message(subject='Solicitud de Insumos',
                  sender=app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[proveedor_email])
    msg.body = "Solicitamos la cotización de los siguientes insumos:\n\n"
    for toner in toners:
        cantidad_necesaria = toner.preferences.min_stock - toner.cantidad_actual
        msg.body += f"Modelo: {toner.modelo}, Cantidad necesaria: {cantidad_necesaria}\n"

    try:
        mail.send(msg)
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

@app.route('/preferences')
def preferences():
    toners = Toner.query.all()
    return render_template('preferences.html', toners=toners)

@app.route('/set_preferences', methods=['POST'])
def set_preferences():
    toner_id = request.form.get('toner_id')
    min_stock = request.form.get('min_stock', type=int)
    proveedor_email = request.form.get('proveedor_email')

    preferences = Preferences.query.filter_by(toner_id=toner_id).first()
    if preferences:
        preferences.min_stock = min_stock
        preferences.proveedor_email = proveedor_email
    else:
        preferences = Preferences(toner_id=toner_id, min_stock=min_stock, proveedor_email=proveedor_email)
        db.session.add(preferences)

    db.session.commit()
    flash('Preferencias actualizadas con éxito', 'success')
    return redirect(url_for('preferences'))

@app.route('/movements')
def movements():
    movimientos = Movement.query.all()  #ver ordenamiento
    return render_template('movements.html', movimientos=movimientos)

@app.route('/revert_movement/<int:movement_id>', methods=['POST'])
def revert_movement(movement_id):
    movimiento = Movement.query.get(movement_id)
    if movimiento:
        toner = Toner.query.get(movimiento.toner_id)
        if movimiento.tipo == 'Salida':
            toner.cantidad_actual += movimiento.cantidad
        elif movimiento.tipo == 'Entrada':
            toner.cantidad_actual -= movimiento.cantidad

        movimiento.reverted = True
        db.session.commit()
        flash('Movimiento revertido con éxito', 'success')
    else:
        flash('Movimiento no encontrado', 'error')

    return redirect(url_for('movements'))

@app.route('/statistics')
def statistics():
    consumos_por_sector = db.session.query(
        Sector.nombre, db.func.sum(Movement.cantidad).label('total_consumido')
    ).join(Movement).filter(Movement.tipo == 'Salida', Movement.reverted == False).group_by(Sector.nombre).all()

    df_consumos = pd.DataFrame(consumos_por_sector, columns=['nombre', 'total_consumido'])
    graph_html = df_consumos.to_html(classes='table table-bordered')

    return render_template('statistics.html', graph_html=graph_html)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
