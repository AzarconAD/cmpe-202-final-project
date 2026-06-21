from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/cpu")
def cpu():
    return render_template("cpu.html")


@app.route("/memory")
def memory():
    return render_template("memory.html")


@app.route("/page-replacement")
def page_replacement():
    return render_template("page.html")


@app.route("/disk")
def disk():
    return render_template("disk.html")


if __name__ == "__main__":
    app.run(debug=True)