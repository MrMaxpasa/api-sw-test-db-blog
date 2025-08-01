import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from src.models import db, User, Character, Planet, Vehicle, Post


def setup_admin(app):
    # Clave secreta y tema
    app.secret_key = os.environ.get('FLASK_APP_KEY', 'sample key')
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

    admin = Admin(app, name='4Geeks Admin', template_mode='bootstrap3')

    # Agregar vistas para todos los modelos
    admin.add_view(ModelView(User, db.session, category='Models'))
    admin.add_view(ModelView(Character, db.session, category='Models'))
    admin.add_view(ModelView(Planet, db.session, category='Models'))
    admin.add_view(ModelView(Vehicle, db.session, category='Models'))
    admin.add_view(ModelView(Post, db.session, category='Models'))
