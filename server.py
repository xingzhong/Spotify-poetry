from flask import Flask, Response, request, jsonify, render_template
from work import spotify
app = Flask(__name__, static_url_path='')


@app.route("/")
def index():
	return render_template("index.html")

@app.route("/search")
def search():
	s = spotify()
	query = request.args.get('q', default="if i can't let it go out of my mind")
	q = s.query(query)
	d = {'iframe':s.render(), 'ret':q, 'q':query, 'ignore':s._ignore, "total":s._c}
	return jsonify(d)

if __name__ == "__main__":
	app.run('0.0.0.0', port = 3000, debug=True)