from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from auth import hash_password, verify_password, create_token, get_current_user
from models import User, Team, Athlete, Match, ScoutEvent, OpponentAnalysis, GamePlan
from schemas import RegisterIn, LoginIn, TeamIn, AthleteIn, MatchIn, ScoutEventIn, OpponentIn, GamePlanIn

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DataInsight Sports Analytics", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"app": "DataInsight Sports Analytics", "status": "online"}

@app.post("/api/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(400, "E-mail já cadastrado")

    user = User(
        name=data.name,
        email=data.email.lower(),
        password_hash=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "token": create_token(user.id, user.role),
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@app.post("/api/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Login inválido")

    return {
        "token": create_token(user.id, user.role),
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@app.post("/api/token")
def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username.lower()).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Login inválido")

    return {
        "access_token": create_token(user.id, user.role),
        "token_type": "bearer"
    }

@app.get("/api/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

def owned(q, user):
    return q.filter_by(owner_id=user.id)

def crud_create(model, payload, user, db):
    obj = model(**payload.model_dump(), owner_id=user.id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@app.get("/api/teams")
def list_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(Team), user).all()

@app.post("/api/teams")
def create_team(data: TeamIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(Team, data, user, db)

@app.delete("/api/teams/{id}")
def delete_team(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(Team), user).filter(Team.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()

    return {"ok": True}

@app.get("/api/athletes")
def list_athletes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(Athlete), user).all()

@app.post("/api/athletes")
def create_athlete(data: AthleteIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(Athlete, data, user, db)

@app.delete("/api/athletes/{id}")
def delete_athlete(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(Athlete), user).filter(Athlete.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()

    return {"ok": True}

@app.get("/api/matches")
def list_matches(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(Match), user).order_by(Match.match_date.desc()).all()

@app.post("/api/matches")
def create_match(data: MatchIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(Match, data, user, db)

@app.delete("/api/matches/{id}")
def delete_match(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(Match), user).filter(Match.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()

    return {"ok": True}

@app.get("/api/scout")
def list_scout(match_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = owned(db.query(ScoutEvent), user)

    if match_id:
        q = q.filter(ScoutEvent.match_id == match_id)

    return q.order_by(ScoutEvent.minute.asc()).all()

@app.post("/api/scout")
def create_scout(data: ScoutEventIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(ScoutEvent, data, user, db)

@app.get("/api/opponents")
def list_opponents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(OpponentAnalysis), user).all()

@app.post("/api/opponents")
def create_opponent(data: OpponentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(OpponentAnalysis, data, user, db)

@app.get("/api/gameplans")
def list_gameplans(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(GamePlan), user).all()

@app.post("/api/gameplans")
def create_gameplan(data: GamePlanIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    opponent = owned(db.query(OpponentAnalysis), user).filter(
        OpponentAnalysis.opponent.ilike(data.opponent)
    ).first()

    suggestion = ""

    if opponent:
        suggestion = (
            f"Adversário costuma jogar em {opponent.base_formation or 'formação não informada'}, "
            f"ataca mais pelo lado {opponent.attack_side or 'não informado'}. "
            f"Recomenda-se explorar fraquezas: {opponent.weaknesses or 'não informadas'}; "
            f"atenção aos pontos fortes: {opponent.strengths or 'não informados'}."
        )

    obj = GamePlan(
        **data.model_dump(),
        ai_suggestion=suggestion,
        owner_id=user.id
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    matches = owned(db.query(Match), user).all()

    total = len(matches)
    wins = sum(1 for m in matches if m.goals_for > m.goals_against)
    draws = sum(1 for m in matches if m.goals_for == m.goals_against)
    losses = total - wins - draws

    gf = sum(m.goals_for for m in matches)
    ga = sum(m.goals_against for m in matches)
    saldo = gf - ga

    aproveitamento = 0
    if total > 0:
        aproveitamento = round(((wins * 3 + draws) / (total * 3)) * 100, 1)

    events = owned(db.query(ScoutEvent), user).all()

    by_event = {}
    for e in events:
        by_event[e.event_type] = by_event.get(e.event_type, 0) + 1

    last_matches = [
        {
            "date": str(m.match_date),
            "opponent": m.opponent,
            "score": f"{m.goals_for} x {m.goals_against}",
            "formation": m.formation or ""
        }
        for m in matches[:5]
    ]

    return {
        "teams": owned(db.query(Team), user).count(),
        "athletes": owned(db.query(Athlete), user).count(),
        "matches": total,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": gf,
        "goals_against": ga,
        "saldo": saldo,
        "aproveitamento": aproveitamento,
        "event_counts": by_event,
        "last_matches": last_matches
    }