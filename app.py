from flask import Flask, render_template, request, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from flask_sqlalchemy import SQLAlchemy
import time
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from threading import Thread

# Initialiser Flask
app = Flask(__name__)

# Configurer SQLAlchemy pour utiliser SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_results.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèle pour la table des résultats de tests
class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.String(100), default=time.strftime('%Y-%m-%d %H:%M:%S'))

# Créer la base de données et la table si elle n'existe pas
with app.app_context():
    db.create_all()

# Fonction pour tester si le site est accessible via Selenium (avec Brave)
def test_with_selenium(url):
    chrome_options = Options()
    chrome_options.binary_location = "C:/Users/abdel/AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe"
    chromedriver_path = "C:/Users/abdel/chromedriver.exe"
    
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(3)  # Attendre que la page se charge
        status = driver.title  # Récupère le titre de la page pour confirmer que le site est en ligne
        driver.quit()
        return f"Le site fonctionne ! Titre de la page : {status}"
    except Exception as e:
        driver.quit()
        return f"❌ Le site n'a pas pu être atteint. Erreur : {str(e)}"

# Fonction pour tester la performance (temps de réponse du site)
def test_performance(url):
    try:
        start_time = time.time()
        response = requests.get(url)
        end_time = time.time()
        duration = end_time - start_time
        status_code = response.status_code
        return f"Temps de réponse : {duration:.2f} secondes (Code HTTP : {status_code})"
    except requests.exceptions.RequestException as e:
        return f"Erreur de connexion : {str(e)}"

# Fonction pour tester la sécurité (si le site utilise HTTPS)
def test_security(url):
    if url.startswith("https"):
        return "Le site utilise HTTPS."
    else:
        return "⚠️ Le site ne semble pas utiliser HTTPS."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test', methods=['POST'])
def test_site():
    url = request.form['url']  # Récupérer l'URL envoyée par le formulaire
    
    if url.startswith("http"):
        # Tester avec Selenium
        selenium_status = test_with_selenium(url)
        
        # Tester la performance
        performance_status = test_performance(url)
        
        # Tester la sécurité
        security_status = test_security(url)
        
        # Combiner les résultats
        status = f"{selenium_status}<br>{performance_status}<br>{security_status}"
        
        # Sauvegarder le résultat dans la base de données
        new_result = TestResult(url=url, status=status)
        db.session.add(new_result)
        db.session.commit()
    else:
        status = "❌ Veuillez entrer une URL valide (commençant par http ou https)."
    
    return render_template('index.html', status=status)

@app.route('/report')
def report():
    # Récupérer tous les résultats de tests depuis la base de données
    results = TestResult.query.all()
    return render_template('report.html', results=results)

@app.route('/download_report')
def download_report():
    # Créer un fichier PDF en mémoire
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 10)

    # Titre du rapport
    c.drawString(100, 750, "Rapport des Tests de Site Web")
    c.drawString(100, 730, "Date: " + time.strftime('%Y-%m-%d %H:%M:%S'))

    # Ajouter les résultats des tests au PDF
    results = TestResult.query.all()
    y_position = 700
    for result in results:
        c.drawString(100, y_position, f"URL: {result.url}")
        c.drawString(100, y_position - 20, f"Statut: {result.status}")
        c.drawString(100, y_position - 40, f"Date et Heure: {result.timestamp}")
        y_position -= 60

        if y_position < 100:
            c.showPage()
            c.setFont("Helvetica", 10)
            y_position = 750

    # Sauvegarder le PDF dans la mémoire
    c.save()

    # Définir la réponse comme un fichier à télécharger
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="rapport_tests.pdf", mimetype="application/pdf")

# Nouvelle route pour supprimer tous les rapports
@app.route('/clear_reports')
def clear_reports():
    try:
        # Supprimer tous les enregistrements de la table TestResult
        TestResult.query.delete()
        db.session.commit()
        return render_template('report.html', status="Tous les rapports ont été supprimés.", results=[])
    except Exception as e:
        return render_template('report.html', status=f"Erreur lors de la suppression des rapports: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
