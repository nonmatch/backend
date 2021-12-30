from flask import Flask, jsonify, redirect, render_template, url_for
from flask_dance.contrib.github import github
from flask_login import logout_user, login_required

from app.models import db, login_manager
from app.oauth import github_blueprint


app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./users.db"
app.register_blueprint(github_blueprint, url_prefix="/login")

db.init_app(app)
login_manager.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def homepage():
    return render_template("index.html")





@app.route("/ping")
def ping():
    return jsonify(ping="pong")


@app.route("/github")
def login():
    if not github.authorized:
        return redirect(url_for("github.login"))
    res = github.get('/user/public_emails')
    print(res.json())


    res = github.get("/user")
    data = res.json()
    print(data)
    if 'message' in data:
        return {'error': data['message']}

    return f"You are @{res.json()['login']} on GitHub"

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("homepage"))

@app.route("/create_pr")
def create_pr():
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.post('/repos/octorock/test/pulls', json={
        'title': 'Test',
        'head': 'nonmatch:nonmatch-patch-1',
        'base': 'main',
        'body': 'This is a test',
        'maintainer_can_modify': True,

    })
    data = res.json()
    print(data)
    if 'message' in data:
        return {'error': data['message']}
    return {'url': data['html_url']}
    return 'ok'

if __name__ == "__main__":
    app.run(debug=True)



