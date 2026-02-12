from flask import Flask
from models import db
from routes.auth_routes import auth_bp
# from routes.admin_routes import admin_bp
# from routes.create_user_routes import createuser_bp
#from routes.user_profile import userprofile_bp
from routes.view_my_profile import profile
from config import Config


def create_app():
    app = Flask(__name__)

    # --------------------------
    # Config
    # --------------------------s
    app.config.from_object(Config)

    # --------------------------
    # Extensions
    # --------------------------
    db.init_app(app)

    # --------------------------
    # Blueprints
    # --------------------------
    app.register_blueprint(auth_bp)
    # app.register_blueprint(admin_bp)
    #app.register_blueprint(userprofile_bp)
    # app.register_blueprint(createuser_bp)
    app.register_blueprint(profile)
   



    return app


app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


