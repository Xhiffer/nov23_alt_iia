from flask import Blueprint, render_template
from flask import render_template

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
@main.route("/blank")
def blank():
    return render_template("blank.html")  # Don't keep the stray "return 'hi'"



"""
404 page
alert page + ajax 
info about the alerte page 
clean up the base page.
"""

@main.app_errorhandler(404)
def page_not_found(error):
    return render_template("404.html"), 404