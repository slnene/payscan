import pyrebase

config = {
    'apiKey': "AIzaSyC_tWpYyEugszcuCAh8UFCWWD-8nZeYS7Q",
    'authDomain': "payscaneswatini.firebaseapp.com",
    'databaseURL': "https://payscaneswatini-default-rtdb.firebaseio.com",
    'projectId': "payscaneswatini",
    'storageBucket': "payscaneswatini.firebasestorage.app",
    'messagingSenderId': "175006917405",
    'appId': "1:175006917405:web:7abfb2aa1c46788c8b77f4",
}
firebase = pyrebase.initialize_app(config)
authe = firebase.auth()
database = firebase.database()