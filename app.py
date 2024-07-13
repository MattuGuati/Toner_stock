import os
import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from fpdf import FPDF
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///toner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'
db = SQLAlchemy(app)

class Toner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(50), unique=True, nullable=False)
    cantidad_actual = db.Column(db.Integer, nullable=False)

class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    toner_id = db.Column(db.Integer, db.ForeignKey('toner.id'), nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    sector_id = db.Column(db.Integer, db.ForeignKey('sector.id'), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    nota = db.Column(db.String(200))

class Sector(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    duracion_predefinida = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

def check_stock_and_send_email():
    low_stock_toners = Toner.query.filter(Toner.cantidad_actual < 2).all()
    if low_stock_toners:
        send_warning_email(low_stock_toners)

def send_warning_email(low_stock_toners):
    sender_email = "apismatteo@gmail.com"
    receiver_email = "apismatteo@gmail.com"
    password = "rlgu byor unnj icwo"

    message = MIMEMultipart("alternative")
    message["Subject"] = "Aviso de Stock de Tóner Bajo"
    message["From"] = sender_email
    message["To"] = receiver_email

    text = "Hola,\n\nEl stock de los siguientes tóners está bajo:\n\n"
    for toner in low_stock_toners:
        text += f"Modelo: {toner.modelo}, Cantidad Actual: {toner.cantidad_actual}\n"
    text += "\nPor favor, revisa el sistema de control de stock para más detalles."

    part = MIMEText(text, "plain")
    message.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())

    flash('Correo de advertencia enviado.', 'success')

@app.route('/')
def index():
    toners = Toner.query.all()
    sectors = Sector.query.all()
    return render_template('index.html', toners=toners, sectors=sectors)

@app.route('/add_toner', methods=['POST'])
def add_toner():
    modelo = request.form['modelo']
    cantidad_actual = int(request.form['cantidad_actual'])

    existing_toner = Toner.query.filter_by(modelo=modelo).first()
    if existing_toner:
        existing_toner.cantidad_actual += cantidad_actual
    else:
        nuevo_toner = Toner(modelo=modelo, cantidad_actual=cantidad_actual)
        db.session.add(nuevo_toner)
    
    db.session.commit()
    check_stock_and_send_email()
    return redirect(url_for('index'))

@app.route('/add_movement', methods=['POST'])
def add_movement():
    toner_id = request.form['toner_id']
    tipo = request.form['tipo']
    cantidad = int(request.form['cantidad'])
    sector_id = request.form['sector_id']
    nota = request.form['nota']

    movimiento = Movimiento(toner_id=toner_id, tipo=tipo, cantidad=cantidad, sector_id=sector_id, nota=nota)
    db.session.add(movimiento)

    toner = Toner.query.get(toner_id)
    if tipo == 'Entrada':
        toner.cantidad_actual += cantidad
    elif tipo == 'Salida':
        toner.cantidad_actual -= cantidad

    db.session.commit()
    check_stock_and_send_email()
    return redirect(url_for('index'))

@app.route('/add_sector', methods=['POST'])
def add_sector():
    nombre = request.form['nombre']
    duracion_predefinida = request.form['duracion_predefinida']

    existing_sector = Sector.query.filter_by(nombre=nombre).first()
    if existing_sector:
        flash('El nombre del sector ya existe. Usa otro nombre.', 'danger')
        return redirect(url_for('index'))

    nuevo_sector = Sector(nombre=nombre, duracion_predefinida=duracion_predefinida)
    db.session.add(nuevo_sector)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/statistics')
def statistics():
    sectors = Sector.query.all()
    consumos_por_sector = []
    predicciones = {}

    for sector in sectors:
        movimientos = Movimiento.query.filter_by(sector_id=sector.id).all()
        total_consumed = sum([m.cantidad for m in movimientos if m.tipo == 'Salida'])
        total_days = (datetime.utcnow() - movimientos[0].fecha).days if movimientos else 0  # Para evitar la división por cero

        consumos_por_sector.append((sector.nombre, total_consumed, sector.duracion_predefinida))

        if total_days > 0:
            predicciones[sector.nombre] = predict_consumption(sector)
        else:
            predicciones[sector.nombre] = "No hay suficiente información para predecir."

    return render_template('statistics.html', consumos=consumos_por_sector, predicciones=predicciones)

def predict_consumption(sector):
    movimientos = Movimiento.query.filter_by(sector_id=sector.id).all()
    total_consumed = sum([m.cantidad for m in movimientos if m.tipo == 'Salida'])
    total_days = (datetime.utcnow() - movimientos[0].fecha).days if movimientos else 1  # Para evitar la división por cero

    daily_consumption_rate = total_consumed / total_days
    remaining_days = sector.duracion_predefinida - total_days
    return daily_consumption_rate * remaining_days

@app.route('/download_report')
def download_report():
    toners = Toner.query.all()
    sectors = Sector.query.all()

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Reporte de Stock de Tóner", ln=True, align='C')

    pdf.cell(200, 10, txt="Stock de Tóner", ln=True, align='L')
    for toner in toners:
        pdf.cell(200, 10, txt=f"{toner.modelo}: {toner.cantidad_actual}", ln=True, align='L')

    pdf.cell(200, 10, txt="Sectores y Duración Predefinida", ln=True, align='L')
    for sector in sectors:
        pdf.cell(200, 10, txt=f"{sector.nombre}: {sector.duracion_predefinida} días", ln=True, align='L')

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    return send_file(pdf_output, attachment_filename='reporte_stock_toner.pdf', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
