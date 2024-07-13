from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///toner_control.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

class Toner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(50), nullable=False, unique=True)
    cantidad_actual = db.Column(db.Integer, nullable=False)

class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    duracion_predefinida = db.Column(db.Integer, nullable=False)

class Movement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    toner_id = db.Column(db.Integer, db.ForeignKey('toner.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=False)
    nota = db.Column(db.String(200), nullable=True)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    toner = db.relationship('Toner', backref=db.backref('movements', lazy=True))
    sector = db.relationship('Sector', backref=db.backref('movements', lazy=True))

@app.before_request
def before_request_func():
    db.create_all()

@app.route('/')
def index():
    toners = Toner.query.all()
    sectors = Sector.query.all()
    return render_template('index.html', toners=toners, sectors=sectors)

@app.route('/add_toner', methods=['POST'])
def add_toner():
    modelo = request.form['modelo']
    cantidad_actual = int(request.form['cantidad_actual'])
    toner = Toner(modelo=modelo, cantidad_actual=cantidad_actual)
    db.session.add(toner)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_sector', methods=['POST'])
def add_sector():
    nombre = request.form['nombre']
    duracion_predefinida = int(request.form['duracion_predefinida'])
    sector = Sector(nombre=nombre, duracion_predefinida=duracion_predefinida)
    db.session.add(sector)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add_movement', methods=['POST'])
def add_movement():
    toner_id = request.form['toner_id']
    tipo = request.form['tipo']
    cantidad = int(request.form['cantidad'])
    sector_id = request.form['sector_id']
    nota = request.form['nota']
    movement = Movement(toner_id=toner_id, tipo=tipo, cantidad=cantidad, sector_id=sector_id, nota=nota)
    db.session.add(movement)

    toner = Toner.query.get(toner_id)
    if tipo == 'Entrada':
        toner.cantidad_actual += cantidad
    elif tipo == 'Salida':
        toner.cantidad_actual -= cantidad

    db.session.commit()

    # Enviar correo si el stock es menor o igual a 2
    if toner.cantidad_actual <= 2:
        flash(f'El stock de {toner.modelo} está por agotarse.', 'warning')

    return redirect(url_for('index'))

@app.route('/statistics')
def statistics():
    sectors = Sector.query.all()
    consumos_por_sector = []
    predicciones = {}
    for sector in sectors:
        movimientos_sector = Movement.query.filter_by(sector_id=sector.id).all()
        total_consumido = sum([mov.cantidad for mov in movimientos_sector if mov.tipo == 'Salida'])
        consumos_por_sector.append((sector.nombre, total_consumido, sector.duracion_predefinida))
        if total_consumido > 0:
            prediccion = sector.duracion_predefinida / total_consumido * 30
            predicciones[sector.nombre] = prediccion
        else:
            predicciones[sector.nombre] = 0

    return render_template('statistics.html', consumos=consumos_por_sector, predicciones=predicciones)

@app.route('/download_report')
def download_report():
    # Crear el PDF
    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(40, 10, 'Reporte de Stock de Tóner')

    # Stock de Tóner
    pdf.set_font('Arial', 'B', 12)
    pdf.ln(10)
    pdf.cell(40, 10, 'Stock de Tóner')
    pdf.set_font('Arial', '', 12)
    toners = Toner.query.all()
    for toner in toners:
        pdf.ln(10)
        pdf.cell(40, 10, f'{toner.modelo}: {toner.cantidad_actual}')

    # Sectores y Duración Predefinida
    pdf.set_font('Arial', 'B', 12)
    pdf.ln(10)
    pdf.cell(40, 10, 'Sectores y Duración Predefinida')
    pdf.set_font('Arial', '', 12)
    sectors = Sector.query.all()
    for sector in sectors:
        pdf.ln(10)
        pdf.cell(40, 10, f'{sector.nombre}: {sector.duracion_predefinida} días')

    # Gráfico de consumos por sector
    consumos_por_sector = {sector.nombre: sum([mov.cantidad for mov in sector.movements if mov.tipo == 'Salida']) for sector in sectors}
    fig, ax = plt.subplots()
    ax.bar(consumos_por_sector.keys(), consumos_por_sector.values())
    ax.set_title('Consumo por Sector')
    ax.set_ylabel('Cantidad')
    ax.set_xlabel('Sector')

    img_path = 'temp_plot.png'
    plt.savefig(img_path)
    plt.close(fig)

    pdf.ln(10)
    pdf.image(img_path, x=None, y=None, w=pdf.w/2)

    # Guardar el archivo PDF
    pdf_output_path = 'reporte_stock_toner.pdf'
    pdf.output(pdf_output_path)

    return send_file(pdf_output_path, as_attachment=True, download_name='reporte_stock_toner.pdf')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
