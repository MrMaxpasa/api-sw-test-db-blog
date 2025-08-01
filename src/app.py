import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS

from src.utils import APIException, generate_sitemap
from src.admin import setup_admin
from src.models import db, User, Character, Planet

app = Flask(__name__)
app.url_map.strict_slashes = False

# Configuración de la base de datos
db_url = os.getenv("DATABASE_URL")
if db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialización de extensiones
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Manejo de errores de API
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Documentación y sitemap
@app.route('/')
def sitemap():
    return generate_sitemap(app)

# ----------------------------
# ENDPOINTS GET EXISTENTES
# ----------------------------

@app.route('/user', methods=['GET'])
def handle_hello():
    return jsonify({"msg": "Hello, this is your GET /user response"}), 200

@app.route('/people', methods=['GET'])
def get_people():
    people = Character.query.all()
    return jsonify([p.serialize() for p in people]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_person(people_id):
    person = Character.query.get(people_id)
    if not person:
        raise APIException('Character not found', status_code=404)
    return jsonify(person.serialize()), 200

@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    return jsonify([p.serialize() for p in planets]), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        raise APIException('Planet not found', status_code=404)
    return jsonify(planet.serialize()), 200

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([u.serialize() for u in users]), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user = User.query.first()
    if not user:
        raise APIException('User not found', status_code=404)

    favorites = {
        'favorite_characters': [c.serialize() for c in user.favorite_characters],
        'favorite_planets':    [p.serialize() for p in user.favorite_planets],
    }
    return jsonify(favorites), 200

# ----------------------------
# CRUD PARA PLANETS
# ----------------------------

@app.route('/planets', methods=['POST'])
def create_planet():
    data = request.get_json() or {}
    required = ['name', 'climate', 'terrain', 'population']
    missing = [f for f in required if f not in data]
    if missing:
        raise APIException(f"Missing fields: {', '.join(missing)}", status_code=400)
    if Planet.query.filter_by(name=data['name']).first():
        raise APIException('Planet with that name already exists', status_code=400)

    planet = Planet(
        name=data['name'],
        climate=data['climate'],
        terrain=data['terrain'],
        population=data['population']
    )
    db.session.add(planet)
    db.session.commit()
    return jsonify(planet.serialize()), 201

@app.route('/planets/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        raise APIException('Planet not found', status_code=404)

    data = request.get_json() or {}
    for field in ['name', 'climate', 'terrain', 'population']:
        if field in data:
            setattr(planet, field, data[field])

    db.session.commit()
    return jsonify(planet.serialize()), 200

@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        raise APIException('Planet not found', status_code=404)

    db.session.delete(planet)
    db.session.commit()
    return jsonify({'message': f'Planet {planet.name} deleted'}), 200

# ----------------------------
# CRUD PARA PEOPLE
# ----------------------------

@app.route('/people', methods=['POST'])
def create_person():
    data = request.get_json() or {}
    required = ['name', 'gender', 'birth_year']
    missing = [f for f in required if f not in data]
    if missing:
        raise APIException(f"Missing fields: {', '.join(missing)}", status_code=400)
    if Character.query.filter_by(name=data['name']).first():
        raise APIException('Character with that name already exists', status_code=400)

    person = Character(
        name=data['name'],
        gender=data['gender'],
        birth_year=data['birth_year'],
        origin_planet_id=data.get('origin_planet_id')
    )
    db.session.add(person)
    db.session.commit()
    return jsonify(person.serialize()), 201

@app.route('/people/<int:people_id>', methods=['PUT'])
def update_person(people_id):
    person = Character.query.get(people_id)
    if not person:
        raise APIException('Character not found', status_code=404)

    data = request.get_json() or {}
    for field in ['name', 'gender', 'birth_year', 'origin_planet_id']:
        if field in data:
            setattr(person, field, data[field])

    db.session.commit()
    return jsonify(person.serialize()), 200

@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_person(people_id):
    person = Character.query.get(people_id)
    if not person:
        raise APIException('Character not found', status_code=404)

    db.session.delete(person)
    db.session.commit()
    return jsonify({'message': f'Character {person.name} deleted'}), 200

# ----------------------------
# ENDPOINTS EXISTENTES DE FAVORITES
# ----------------------------

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user = User.query.first()
    planet = Planet.query.get(planet_id)
    if not planet:
        raise APIException('Planet not found', status_code=404)
    if planet in user.favorite_planets:
        raise APIException('Planet already in favorites', status_code=400)
    user.favorite_planets.append(planet)
    db.session.commit()
    return jsonify({'message': f'Planet {planet.name} added to favorites'}), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_person(people_id):
    user = User.query.first()
    person = Character.query.get(people_id)
    if not person:
        raise APIException('Character not found', status_code=404)
    if person in user.favorite_characters:
        raise APIException('Character already in favorites', status_code=400)
    user.favorite_characters.append(person)
    db.session.commit()
    return jsonify({'message': f'Character {person.name} added to favorites'}), 201

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def remove_favorite_planet(planet_id):
    user = User.query.first()
    planet = Planet.query.get(planet_id)
    if not planet:
        raise APIException('Planet not found', status_code=404)
    if planet not in user.favorite_planets:
        raise APIException('Planet not in favorites', status_code=400)
    user.favorite_planets.remove(planet)
    db.session.commit()
    return jsonify({'message': f'Planet {planet.name} removed from favorites'}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def remove_favorite_person(people_id):
    user = User.query.first()
    person = Character.query.get(people_id)
    if not person:
        raise APIException('Character not found', status_code=404)
    if person not in user.favorite_characters:
        raise APIException('Character not in favorites', status_code=400)
    user.favorite_characters.remove(person)
    db.session.commit()
    return jsonify({'message': f'Character {person.name} removed from favorites'}), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)