from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
import pandas as pd  
from models import db, Toner, Movement, Sector, Preferences
#import from controlers
from controlers.movementcontroler import all_movements, rev_movement, new_movement
from controlers.tonercontroler import all_toners, one_toner, plus_toner, less_toner
from controlers.sectorcontroler import all_sectors, del_sector, add_sector

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
migrate = Migrate(app, db)
mail = Mail(app)

#!---index---!
@app.route('/')
def index():
    return render_template('index.html', toners = all_toners(), sectors = all_sectors())

#!---insumos---!
@app.route('/salida_insunmo', methods=['GET','POST'])
def salida_insumo():
    if request.method == 'POST':
        toner_id = request.form.get('toner_id')
        sector_id = request.form.get('sector_id')
        cantidad = request.form.get('cantidad', type=int)
    
        if less_toner(toner_id, cantidad):
            return redirect(url_for('salida_insumo'))

        new_movement('Salida', cantidad, toner_id, sector_id)
    return render_template('salida_insumo.html', toners = all_toners(), sectors = all_sectors())

@app.route('/entrada_insumo', methods=['GET','POST'])
def entrada_insumo():
    if request.method == 'POST':
        toner_id = request.form.get('toner_id')
        cantidad = request.form.get('cantidad', type=int)
        
        if plus_toner(toner_id, cantidad):
            return redirect(url_for('entrada_insumo'))
    
        new_movement('Entrada', cantidad, toner_id)
    return render_template('entrada_insumo.html', toners= all_toners())

@app.route('/solicitar_insumos', methods=['GET', 'POST'])
def solicitar_insumos():
    if request.method == 'POST':
        toner_ids = request.form.getlist('toners')
        pedidos = {}

        for toner_id in toner_ids:
            toner = one_toner(toner_id)
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
    return render_template('preferences.html', all_toners())

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

#!---movimientos---!
@app.route('/movements')
def movements():
    return render_template('movements.html', movimientos = all_movements())

@app.route('/revert_movement/<int:movement_id>', methods=['POST'])
def revert_movement(movement_id):
    rev_movement(movement_id)
    return redirect(url_for('movements'))

#!---sectores---!
@app.route('/sectores')
def sectores():
    return render_template('sectores.html', sectores = all_sectors())

@app.route('/delete_sector/<int:sector_id>', methods=['POST'])
def delete_sector(sector_id):
    del_sector(sector_id)
    return redirect(url_for('sectores'))

@app.route('/alta_sector', methods=['POST'])
def alta_sector():
    if request.method == 'POST':
        sector_name = request.form.get('sector_name')
        duracion_predefinida = request.form.get('duracion_predefinida', type= int)
        
        if not sector_name or not duracion_predefinida:
            flash('Por favor, complete todos los campos.', 'danger')
            return redirect(url_for('sectores'))

        try:
            # Crear un nuevo sector
            add_sector(sector_name, duracion_predefinida)
            flash('Sector registrado exitosamente.', 'success')
            return redirect(url_for('sectores'))   
        
        except Exception as e:
            db.session.rollback()  # Revertir cambios si hay un error
            flash(f'Error al registrar el sector: {e}', 'danger')


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
