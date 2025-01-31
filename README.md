Voici une documentation complète pour votre projet. Cette documentation couvre l'installation, l'architecture du projet, la description des fonctionnalités, ainsi que les détails techniques.

---

# Documentation du Projet - Outil de Test de Site Web

## Introduction

Ce projet est une application web permettant de tester des sites Web à travers trois critères principaux :
1. **Disponibilité du site (via Selenium)**
2. **Performance (temps de réponse HTTP)**
3. **Sécurité (HTTPS)**

Les utilisateurs peuvent tester des sites, visualiser les résultats sous forme de rapports, et télécharger ces rapports au format PDF ou CSV.

---

## Prérequis

Avant d'exécuter l'application, assurez-vous d'avoir les prérequis suivants :

- **Python 3.x** : Vous pouvez télécharger Python [ici](https://www.python.org/downloads/).
- **Bibliothèques Python nécessaires** :
    - Flask
    - Flask-SQLAlchemy
    - Flask-Login
    - Selenium
    - Requests
    - ReportLab
    - Werkzeug
    - CSV

Vous pouvez installer les bibliothèques nécessaires avec la commande suivante :
```bash
pip install flask flask_sqlalchemy flask_login selenium requests reportlab
```

De plus, vous devez avoir **ChromeDriver** et **Brave Browser** installés sur votre machine pour que Selenium puisse effectuer les tests de site.

- Téléchargez **ChromeDriver** [ici](https://sites.google.com/a/chromium.org/chromedriver/downloads) en fonction de votre version de Chrome.
- **Brave Browser** est utilisé comme alternative à Chrome et peut être téléchargé [ici](https://brave.com/download/).

---

## Structure du Projet

Voici l'architecture de fichiers de votre projet :

```
/test-web-app/
├── app.py                # Fichier principal de l'application Flask
├── /templates/           # Dossier contenant les fichiers HTML
│   ├── index.html        # Page d'accueil avec le formulaire de test
│   ├── report.html       # Page de rapport avec les résultats des tests
│   └── login.html        # Page de connexion
├── /static/              # Dossier contenant les fichiers CSS
│   └── styles.css        # Styles personnalisés
└── /instance/            # Dossier contenant la base de données SQLite
    └── test_results.db   # Base de données contenant les résultats des tests
```

---

## Description des Fonctionnalités

### 1. **Page d'Accueil (`index.html`)**
- **Formulaire de Test** : Permet à l'utilisateur de saisir l'URL d'un site Web pour le tester.
- **Exécution du Test** : Lors de la soumission du formulaire, un test est effectué sur l'URL saisie, incluant la vérification de la disponibilité du site, la performance et la sécurité.
- **Résultats** : Les résultats sont affichés immédiatement après le test. Si l'URL est invalide, un message d'erreur est affiché.

### 2. **Page de Rapport (`report.html`)**
- **Liste des Résultats** : Affiche les rapports des tests précédemment effectués, avec les colonnes suivantes :
  - URL du site testé
  - Statut du test (fonctionnement, temps de réponse, sécurité)
  - Date et heure du test
- **Téléchargement des Rapports** : Permet de télécharger les rapports au format **PDF** ou **CSV**.
- **Suppression des Rapports** : Un bouton pour supprimer tous les rapports existants.

### 3. **Page de Connexion (`login.html`)**
- **Authentification** : L'accès à la page des rapports est sécurisé. Les utilisateurs doivent se connecter avec un nom d'utilisateur et un mot de passe pour y accéder.
- **Gestion des utilisateurs** : L'utilisateur "admin" est créé par défaut lors de la première utilisation de l'application.

### 4. **Tests de Site**
Le système effectue trois types de tests :
- **Test de Fonctionnement** : Utilisation de **Selenium** pour vérifier si le site est accessible et obtenir le titre de la page.
- **Test de Performance** : Utilisation de **Requests** pour mesurer le temps de réponse du site.
- **Test de Sécurité** : Vérification si l'URL commence par **https://** pour déterminer si la connexion est sécurisée.

---

## Détails Techniques

### 1. **Backend (Flask)**
L'application utilise **Flask**, un framework web léger pour Python. Les principales fonctionnalités du backend incluent :
- **Routes** :
    - `/` : Page d'accueil avec le formulaire de test.
    - `/test` : Effectue le test sur l'URL soumise.
    - `/report` : Affiche les rapports de tests précédents.
    - `/download_report/pdf` : Télécharge le rapport des tests sous forme de fichier PDF.
    - `/download_report/csv` : Télécharge le rapport des tests sous forme de fichier CSV.
    - `/clear_reports` : Supprime tous les rapports enregistrés dans la base de données.
    - `/login` : Page de connexion.
    - `/logout` : Déconnexion de l'utilisateur.

- **Base de données (SQLAlchemy)** : Utilisation de **SQLite** pour stocker les résultats des tests dans une base de données locale (`test_results.db`). Chaque rapport de test est sauvegardé avec l'URL, le statut, et la date du test.
  
- **Sécurisation de l'Accès** : Utilisation de **Flask-Login** pour gérer l'authentification des utilisateurs. Seul l'utilisateur connecté peut accéder à la page des rapports.

### 2. **Tests de Site avec Selenium**
L'application utilise **Selenium** pour tester la disponibilité du site en visitant l'URL dans un navigateur sans interface graphique (mode "headless"). Le titre de la page est récupéré pour déterminer si le site fonctionne correctement.

**Exemple de code** pour tester le fonctionnement d'un site :
```python
def test_with_selenium(url):
    options = Options()
    options.add_argument('--headless')  # Mode sans interface graphique
    options.binary_location = "C:/Path/To/BraveBrowser"
    chromedriver_path = "C:/Path/To/chromedriver"
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
```

### 3. **Test de Performance avec Requests**
Le temps de réponse est mesuré en envoyant une requête **HTTP GET** à l'URL et en mesurant la durée de la réponse.

**Exemple de code** pour tester la performance d'un site :
```python
def test_performance(url):
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        duration = time.time() - start_time
        return f"⏳ Temps de réponse : {duration:.2f} sec (HTTP {response.status_code})"
    except requests.exceptions.RequestException as e:
        return f"⚠️ Erreur de connexion : {str(e)}"
```

### 4. **Test de Sécurité**
Un simple test vérifie si l'URL commence par `https` pour indiquer que la connexion est sécurisée.

**Exemple de code** :
```python
def test_security(url):
    return "🔒 HTTPS activé" if url.startswith("https") else "⚠️ HTTPS non activé"
```

---

## Sécurisation de l'Application

- **Connexion et authentification** : L'authentification est gérée par **Flask-Login**. Un utilisateur `admin` est créé par défaut avec un mot de passe sécurisé.
- **Gestion des sessions** : Flask utilise un cookie de session pour garder une trace de l'utilisateur connecté.

---

## Conclusion

Ce projet est un outil simple et efficace pour tester des sites Web, avec une interface claire permettant de consulter les résultats des tests et de les exporter en PDF ou CSV. L'utilisation de **Selenium**, **Requests**, et **Flask** permet de créer une application web interactive qui peut être étendue et modifiée pour des besoins futurs.

---

## Pour aller plus loin

- **Amélioration de l'interface utilisateur** : Ajouter des graphiques pour visualiser les performances.
- **Tests supplémentaires** : Ajouter des tests pour des aspects comme la SEO, la compatibilité mobile, ou des tests de sécurité plus poussés.
- **Déploiement** : Vous pouvez déployer cette application sur un serveur avec un fournisseur comme **Heroku** ou **AWS** pour l'utiliser en production.


*********************
![alt text](static/image.png)
![alt text](static/image1.png)
![alt text](static/image2.png)
![alt text](static/image3.png)