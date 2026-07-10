import os
import uuid
import json
from datetime import datetime, timedelta, date
from functools import wraps

from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

db_url = os.environ.get("DATABASE_URL", "sqlite:///local_dev.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

db = SQLAlchemy(app)

TEAM_PASSWORD = os.environ.get("TEAM_PASSWORD", "ronda2026")

TRIGGERS = [
    "Withdrawn/deleted shift with no clear reason",
    '"Ongoing" language vs thin booking history',
    "Payment-chasing enquiry for off-platform shift",
    "Booking activity dropped off after one placement",
    "Contact details exchanged unusually early",
    'Language suggesting arranging "directly"/"outside"',
    "Third-party report (locum/practice/staff)",
    "Locum failed to report direct practice contact (15.4)",
]


class Case(db.Model):
    __tablename__ = "cases"
    id = db.Column(db.String(40), primary_key=True)
    party_type = db.Column(db.String(20))
    practice_name = db.Column(db.String(255))
    locum_names = db.Column(db.String(255))
    date_flagged = db.Column(db.String(20))
    flagged_by = db.Column(db.String(50))
    triggers = db.Column(db.Text)
    evidence_summary = db.Column(db.Text)
    evidence_location = db.Column(db.String(255))
    outcome = db.Column(db.String(50))
    stage = db.Column(db.String(30))
    stage1_sent = db.Column(db.String(20))
    stage1_deadline = db.Column(db.String(20))
    complied = db.Column(db.String(20))
    stage2_date = db.Column(db.String(20))
    stage2_decision = db.Column(db.String(30))
    fee_amount = db.Column(db.String(20))
    bonus_affected = db.Column(db.String(10))
    stage3_date = db.Column(db.String(20))
    stage4_date = db.Column(db.String(20))
    account_status = db.Column(db.String(20))
    repeat_case = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text, default="[]")
    created_at = db.Column(db.String(30))
    updated_at = db.Column(db.String(30))
    updated_by = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "partyType": self.party_type,
            "practiceName": self.practice_name,
            "locumNames": self.locum_names,
            "dateFlagged": self.date_flagged,
            "flaggedBy": self.flagged_by,
            "triggers": json.loads(self.triggers or "[]"),
            "evidenceSummary": self.evidence_summary,
            "evidenceLocation": self.evidence_location,
            "outcome": self.outcome,
            "stage": self.stage,
            "stage1Sent": self.stage1_sent,
            "stage1Deadline": self.stage1_deadline,
            "complied": self.complied,
            "stage2Date": self.stage2_date,
            "stage2Decision": self.stage2_decision,
            "feeAmount": self.fee_amount,
            "bonusAffected": self.bonus_affected,
            "stage3Date": self.stage3_date,
            "stage4Date": self.stage4_date,
            "accountStatus": self.account_status,
            "repeatCase": bool(self.repeat_case),
            "notes": json.loads(self.notes or "[]"),
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
            "updatedBy": self.updated_by,
        }


class KBArticle(db.Model):
    __tablename__ = "kb_articles"
    id = db.Column(db.String(40), primary_key=True)
    title = db.Column(db.String(255))
    category = db.Column(db.String(100))
    content = db.Column(db.Text)
    author = db.Column(db.String(50))
    created_at = db.Column(db.String(30))
    updated_at = db.Column(db.String(30))

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "author": self.author,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


with app.app_context():
    db.create_all()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("authed"):
            if request.path.startswith("/api/"):
                return jsonify({"error": "not authenticated"}), 401
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def add_working_days(start_str, days):
    if not start_str:
        return ""
    try:
        d = datetime.strptime(start_str, "%Y-%m-%d").date()
    except ValueError:
        return ""
    added = 0
    while added < days:
        d += timedelta(days=1)
        if d.weekday() < 5:
            added += 1
    return d.isoformat()


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        if password == TEAM_PASSWORD and name:
            session["authed"] = True
            session["who"] = name
            return redirect(url_for("index"))
        error = "Incorrect password, or missing name."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html", who=session.get("who", ""), triggers=TRIGGERS)


@app.route("/kb")
@login_required
def kb_page():
    return render_template("kb.html", who=session.get("who", ""))


# ---------------- Case API ----------------

@app.route("/api/cases", methods=["GET"])
@login_required
def list_cases():
    rows = Case.query.order_by(Case.date_flagged.desc()).all()
    return jsonify([r.to_dict() for r in rows])


@app.route("/api/cases", methods=["POST"])
@login_required
def create_case():
    data = request.get_json(force=True)
    cid = data.get("id") or str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    existing = Case.query.get(cid)
    c = existing or Case(id=cid, created_at=now)
    c.party_type = data.get("partyType")
    c.practice_name = data.get("practiceName")
    c.locum_names = data.get("locumNames")
    c.date_flagged = data.get("dateFlagged")
    c.flagged_by = data.get("flaggedBy")
    c.triggers = json.dumps(data.get("triggers", []))
    c.evidence_summary = data.get("evidenceSummary")
    c.evidence_location = data.get("evidenceLocation")
    c.outcome = data.get("outcome")
    c.stage = data.get("stage")
    c.stage1_sent = data.get("stage1Sent")
    c.stage1_deadline = data.get("stage1Deadline") or add_working_days(data.get("stage1Sent"), 3)
    c.complied = data.get("complied")
    c.stage2_date = data.get("stage2Date")
    c.stage2_decision = data.get("stage2Decision")
    c.fee_amount = str(data.get("feeAmount") or "")
    c.bonus_affected = data.get("bonusAffected")
    c.stage3_date = data.get("stage3Date")
    c.stage4_date = data.get("stage4Date")
    c.account_status = data.get("accountStatus")
    c.repeat_case = bool(data.get("repeatCase"))
    c.notes = json.dumps(data.get("notes", []))
    c.updated_at = now
    c.updated_by = session.get("who", "Unknown")
    if not existing:
        db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict())


@app.route("/api/cases/<cid>", methods=["DELETE"])
@login_required
def delete_case(cid):
    c = Case.query.get(cid)
    if c:
        db.session.delete(c)
        db.session.commit()
    return jsonify({"deleted": True})


@app.route("/api/working-days-deadline", methods=["GET"])
@login_required
def working_days_deadline():
    start = request.args.get("start", "")
    return jsonify({"deadline": add_working_days(start, 3)})


# ---------------- Knowledge Base API ----------------

@app.route("/api/kb", methods=["GET"])
@login_required
def list_kb():
    rows = KBArticle.query.order_by(KBArticle.updated_at.desc()).all()
    return jsonify([r.to_dict() for r in rows])


@app.route("/api/kb", methods=["POST"])
@login_required
def create_kb():
    data = request.get_json(force=True)
    kid = data.get("id") or str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    existing = KBArticle.query.get(kid)
    a = existing or KBArticle(id=kid, created_at=now)
    a.title = data.get("title")
    a.category = data.get("category")
    a.content = data.get("content")
    a.author = session.get("who", "Unknown")
    a.updated_at = now
    if not existing:
        db.session.add(a)
    db.session.commit()
    return jsonify(a.to_dict())


@app.route("/api/kb/<kid>", methods=["DELETE"])
@login_required
def delete_kb(kid):
    a = KBArticle.query.get(kid)
    if a:
        db.session.delete(a)
        db.session.commit()
    return jsonify({"deleted": True})


if __name__ == "__main__":
    app.run(debug=True, port=5050)
