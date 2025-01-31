from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, session, flash
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import time
import requests
import csv
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Initialiser Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_results.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser la base de données
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Modèle utilisateur
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Modèle pour les résultats de test
class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.String(100), default=time.strftime('%Y-%m-%d %H:%M:%S'))

# Création de la base de données
with app.app_context():
    db.create_all()

    # Ajouter un utilisateur "admin" par défaut si aucun utilisateur n'est trouvé dans la base de données
    if not User.query.first():
        hashed_password = generate_password_hash('password123')
        admin = User(username='admin', password=hashed_password)
        db.session.add(admin)
        db.session.commit()

def test_with_selenium(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    
    # Spécifiez le chemin vers Brave
    options.binary_location = "C:/Users/abdel/AppData/Local/BraveSoftware/Brave-Browser/Application/brave.exe"  # Remplacez ce chemin par le vôtre
    chromedriver_path = "C:/Users/abdel/chromedriver.exe"
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        status = driver.title
        driver.quit()
        return f"✅ Le site fonctionne ! Titre de la page : {status}"
    except Exception as e:
        driver.quit()
        return f"❌ Erreur : {str(e)}"

def test_performance(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        duration = time.time() - start_time
        return f"⏳ Temps de réponse : {duration:.2f} sec (HTTP {response.status_code})"
    except requests.exceptions.RequestException as e:
        return f"⚠️ Erreur de connexion : {str(e)}"

def test_security(url):
    return "🔒 HTTPS activé" if url.startswith("https") else "⚠️ HTTPS non activé"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test', methods=['POST'])
@login_required
def test_site():
    url = request.form['url']
    if url.startswith("http"):
        # Utiliser des paragraphes ou d'autres balises pour un formatage plus propre
        results = f"<p>{test_with_selenium(url)}</p><p>{test_performance(url)}</p><p>{test_security(url)}</p>"
        
        new_result = TestResult(url=url, status=results)
        db.session.add(new_result)
        db.session.commit()
        flash("Test effectué avec succès!", "success")
    else:
        results = "<p>❌ URL invalide.</p>"
    return render_template('index.html', status=results)


@app.route('/report')
@login_required
def report():
    results = TestResult.query.all()
    if results:
        return render_template('report.html', results=results)
    else:
        flash("Aucun rapport trouvé.", "warning")
        return render_template('report.html', results=None)

@app.route('/download_report/pdf')
@login_required
def download_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 10)
    c.drawString(100, 750, "Rapport des Tests Web")
    c.drawString(100, 730, f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    results = TestResult.query.all()
    y_position = 700
    for result in results:
        c.drawString(100, y_position, f"URL: {result.url}")
        c.drawString(100, y_position - 20, f"Statut: {result.status}")
        c.drawString(100, y_position - 40, f"Date: {result.timestamp}")
        y_position -= 60
        if y_position < 100:
            c.showPage()
            y_position = 750
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="rapport_tests.pdf", mimetype="application/pdf")

@app.route('/download_report/csv')
@login_required
def download_csv():
    buffer = BytesIO()
    writer = csv.writer(buffer)
    writer.writerow(["URL", "Statut", "Date"])
    results = TestResult.query.all()
    for result in results:
        writer.writerow([result.url, result.status, result.timestamp])
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="rapport_tests.csv", mimetype="text/csv")

@app.route('/clear_reports', methods=['POST'])
@login_required
def clear_reports():
    TestResult.query.delete()
    db.session.commit()
    flash("Tous les rapports ont été supprimés.", "success")
    return redirect(url_for('report'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('report'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == '__main__':
    app.run(debug=True)
