from flask import Blueprint, render_template

main = Blueprint(
    "main",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/"
)

@main.route("/")
def home():
    return render_template("index.html")  # Don't keep the stray "return 'hi'"

@main.route("/about")
def about():
    return render_template("about.html")
