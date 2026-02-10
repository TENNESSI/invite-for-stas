import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Flask, render_template, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///rsvp.sqlite3")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class RSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    fio = db.Column(db.String(255), nullable=True)
    attending = db.Column(db.Boolean, nullable=True)
    alcohol = db.Column(db.String(255), nullable=True)

    data_json = db.Column(db.Text, nullable=False)
    ip = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)


with app.app_context():
    db.create_all()


def _first_nonempty(values):
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return None


def _extract_fields(form: Dict[str, Any]) -> Dict[str, Optional[str]]:
    '''
    We store all fields as JSON. Additionally we try to extract key values for admin view.
    Supports our native Flask form keys (fio/attending/food/alcohol) and also legacy Tilda labels.
    '''
    # Native Flask form
    fio = _first_nonempty([form.get('fio'), form.get('name')])
    attending_raw = _first_nonempty([form.get('attending')])
    alcohol = _first_nonempty([form.get('alcohol')])

    if any([fio, attending_raw, alcohol]):
        attending = None
        if attending_raw:
            s = attending_raw.strip().lower()
            if 'приду' in s or s in ('yes','да','true','1'):
                attending = True
            if 'не получится' in s or 'не смогу' in s or s in ('no','нет','false','0'):
                attending = False
        return {'fio': fio, 'attending': attending, 'alcohol': alcohol}

    keys = list(form.keys())

    fio_key = None
    for k in keys:
        lk = k.lower()
        if "фио" in lk or lk == "name" or "имя" in lk:
            fio_key = k
            break

    attending_key = None
    for k in keys:
        lk = k.lower()
        if "сможете" in lk or "присутств" in lk or "attend" in lk:
            attending_key = k
            break

    alcohol_key = None
    for k in keys:
        lk = k.lower()
        if "алког" in lk or "alcohol" in lk:
            alcohol_key = k
            break

    fio = _first_nonempty([form.get(fio_key)]) if fio_key else None
    attending_raw = _first_nonempty([form.get(attending_key)]) if attending_key else None
    alcohol = _first_nonempty([form.get(alcohol_key)]) if alcohol_key else None

    attending = None
    if attending_raw:
        s = attending_raw.strip().lower()
        if "приду" in s or s in ("yes", "да", "true", "1"):
            attending = True
        if "не получится" in s or "не смогу" in s or s in ("no", "нет", "false", "0"):
            attending = False

    return {"fio": fio, "attending": attending, "alcohol": alcohol}


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/rsvp")
def rsvp():
    form = {k: request.form.get(k) for k in request.form.keys()}
    meaningful = {k: v for k, v in form.items() if k and not k.startswith("_")}
    if not meaningful:
        return jsonify({"ok": False, "error": "Пустая форма"}), 400

    fields = _extract_fields(meaningful)

    rec = RSVP(
        fio=fields["fio"],
        attending=fields["attending"],
        alcohol=fields["alcohol"],
        data_json=json.dumps(meaningful, ensure_ascii=False),
        ip=request.headers.get("X-Forwarded-For", request.remote_addr),
        user_agent=request.headers.get("User-Agent"),
    )
    db.session.add(rec)
    db.session.commit()

    return jsonify({"ok": True})


@app.get("/df029efhj09wquednfh-9awd8fh-v9a")
def admin():
    token = os.environ.get("ADMIN_TOKEN")
    if token and request.args.get("token") != token:
        abort(403)

    rows = RSVP.query.order_by(RSVP.created_at.desc()).all()
    view_rows = []
    for r in rows:
        view_rows.append(
            dict(
                created_at=r.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                fio=r.fio,
                attending=r.attending,
                alcohol=r.alcohol,
                data_json=r.data_json,
            )
        )
    return render_template("admin.html", rows=view_rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)