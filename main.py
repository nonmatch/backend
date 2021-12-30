
from flask import Flask, jsonify, redirect, url_for
from flask_dance.contrib.github import github

from app.oauth import github_blueprint


app = Flask(__name__)
app.secret_key = "supersecretkey"
app.register_blueprint(github_blueprint, url_prefix="/login")


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