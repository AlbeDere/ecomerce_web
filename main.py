from flask import Flask, render_template
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)

@app.route('/')
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/terms_of_service")
def terms_of_service():
    return render_template("tos.html")

@app.route("/privacy_policy")
def privacy_policy():
    return render_template("pp.html")


if __name__ == '__main__':
    app.run(debug=True)