import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate('payscan/credentials.json')
firebase_admin.initialize_app(cred)
