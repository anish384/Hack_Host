import os
import datetime
from flask import Flask
from flask_mail import Mail
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        MONGO_URI='mongodb+srv://anishdesai:264742@cluster0.ijfacnv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0/StarterFlask',
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from flask import g, render_template, redirect, url_for
    @app.route('/')
    def index():
        if getattr(g, 'user', None):
            # Check if student profile is complete
            if g.user.get('user_type') == 'student' and not g.user.get('profile_complete', False):
                return redirect(url_for('profile.student_profile'))
            # Check if recruiter profile is complete
            elif g.user.get('user_type') == 'recruiter' and not g.user.get('profile_complete', False):
                return redirect(url_for('profile.recruiter_profile'))
            username = g.user['username']
        else:
            username = None
        return render_template('index.html', username=username)

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    # Initialize database indexes
    auth.init_db_indexes(app)

    # Register admin blueprint
    from . import admin
    app.register_blueprint(admin.bp)


    # Create first admin user if none exists
    with app.app_context():
        database = db.get_db()
        admin_exists = database['users'].find_one({'is_admin': True})
        if not admin_exists:
            # Check if any user exists that we can promote to admin
            first_user = database['users'].find_one({})
            if first_user:
                database['users'].update_one(
                    {'_id': first_user['_id']},
                    {'$set': {'is_admin': True}}
                )
                from flaskr.admin_log import log_admin_event
                log_admin_event('admin_creation', f'User {first_user.get("email")} automatically promoted to admin as first admin user')
    
    from . import profile
    app.register_blueprint(profile.bp)
    
    # Register jobs blueprint
    from . import jobs
    app.register_blueprint(jobs.bp)
    
    # Register applications blueprint
    from . import applications
    app.register_blueprint(applications.bp)

    return app
