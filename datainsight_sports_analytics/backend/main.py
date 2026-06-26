from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from xml.sax.saxutils import escape
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from auth import hash_password, verify_password, create_token, get_current_user
from models import User, Team, Athlete, Match, ScoutEvent, OpponentAnalysis, GamePlan
from schemas import RegisterIn, LoginIn, TeamIn, AthleteIn, MatchIn, ScoutEventIn, OpponentIn, GamePlanIn

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DataInsight Sports Analytics", version="1.1.0")

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

def crud_update(model, obj_id, payload, user, db):
    obj = owned(db.query(model), user).filter(model.id == obj_id).first()

    if not obj:
        raise HTTPException(404, "Não encontrado")

    for key, value in payload.model_dump().items():
        setattr(obj, key, value)

    db.commit()
    db.refresh(obj)
    return obj

# TIMES
@app.get("/api/teams")
def list_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(Team), user).all()

@app.post("/api/teams")
def create_team(data: TeamIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(Team, data, user, db)

@app.put("/api/teams/{id}")
def update_team(id: int, data: TeamIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_update(Team, id, data, user, db)

@app.delete("/api/teams/{id}")
def delete_team(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(Team), user).filter(Team.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()
    return {"ok": True}

# ATLETAS
@app.get("/api/athletes")
def list_athletes(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(Athlete), user).all()

@app.post("/api/athletes")
def create_athlete(data: AthleteIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(Athlete, data, user, db)

@app.put("/api/athletes/{id}")
def update_athlete(id: int, data: AthleteIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_update(Athlete, id, data, user, db)

@app.delete("/api/athletes/{id}")
def delete_athlete(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(Athlete), user).filter(Athlete.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()
    return {"ok": True}

# JOGOS
@app.get("/api/matches")
def list_matches(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(Match), user).order_by(Match.match_date.desc()).all()

@app.post("/api/matches")
def create_match(data: MatchIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(Match, data, user, db)

@app.put("/api/matches/{id}")
def update_match(id: int, data: MatchIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_update(Match, id, data, user, db)

@app.delete("/api/matches/{id}")
def delete_match(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(Match), user).filter(Match.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()
    return {"ok": True}

# SCOUT
@app.get("/api/scout")
def list_scout(match_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = owned(db.query(ScoutEvent), user)

    if match_id:
        q = q.filter(ScoutEvent.match_id == match_id)

    return q.order_by(ScoutEvent.minute.asc()).all()

@app.post("/api/scout")
def create_scout(data: ScoutEventIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(ScoutEvent, data, user, db)

@app.put("/api/scout/{id}")
def update_scout(id: int, data: ScoutEventIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_update(ScoutEvent, id, data, user, db)

@app.delete("/api/scout/{id}")
def delete_scout(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(ScoutEvent), user).filter(ScoutEvent.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()
    return {"ok": True}
    
# ========= EXPORTAR SCOUT CSV =========

from fastapi.responses import StreamingResponse
import csv

@app.get("/api/scout/csv")
def export_scout_csv(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    eventos = owned(db.query(ScoutEvent), user).order_by(ScoutEvent.minute.asc()).all()

    output = BytesIO()
    text = output.write

    import io

    csv_buffer = io.StringIO()

    writer = csv.writer(csv_buffer)

    writer.writerow([
        "Minuto",
        "Atleta",
        "Evento",
        "Zona",
        "Resultado",
        "Observações"
    ])

    atletas = {
        a.id: a.name
        for a in owned(db.query(Athlete), user).all()
    }

    for e in eventos:

        writer.writerow([
            e.minute,
            atletas.get(e.athlete_id, ""),
            e.event_type,
            e.zone,
            e.result,
            e.notes
        ])

    bytes_buffer = BytesIO(csv_buffer.getvalue().encode("utf-8-sig"))

    return StreamingResponse(
        bytes_buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=scout.csv"
        }
    )    

# ADVERSÁRIOS
@app.get("/api/opponents")
def list_opponents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return owned(db.query(OpponentAnalysis), user).all()

@app.post("/api/opponents")
def create_opponent(data: OpponentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_create(OpponentAnalysis, data, user, db)

@app.put("/api/opponents/{id}")
def update_opponent(id: int, data: OpponentIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return crud_update(OpponentAnalysis, id, data, user, db)

@app.delete("/api/opponents/{id}")
def delete_opponent(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(OpponentAnalysis), user).filter(OpponentAnalysis.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()
    return {"ok": True}

# PLANOS DE JOGO
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

@app.put("/api/gameplans/{id}")
def update_gameplan(id: int, data: GamePlanIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(GamePlan), user).filter(GamePlan.id == id).first()

    if not obj:
        raise HTTPException(404, "Não encontrado")

    for key, value in data.model_dump().items():
        setattr(obj, key, value)

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

    obj.ai_suggestion = suggestion

    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/api/gameplans/{id}")
def delete_gameplan(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    obj = owned(db.query(GamePlan), user).filter(GamePlan.id == id).first()
    if not obj:
        raise HTTPException(404, "Não encontrado")

    db.delete(obj)
    db.commit()
    return {"ok": True}

# ========= RELATÓRIOS PDF =========

def safe_text(value):
    return escape(str(value or "Não informado."))

def make_pdf_response(title_text, subtitle_text, info_rows, sections, filename):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title = ParagraphStyle(
        "PDFTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#0f766e"),
        alignment=1,
        spaceAfter=14
    )

    subtitle = ParagraphStyle(
        "PDFSubtitle",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8
    )

    normal = ParagraphStyle(
        "PDFNormal",
        parent=styles["Normal"],
        fontSize=10,
        leading=14
    )

    story = []
    story.append(Paragraph("DataInsight Sports Analytics PRO", title))
    story.append(Paragraph(safe_text(subtitle_text), subtitle))
    story.append(Spacer(1, 12))

    if info_rows:
        info = [[safe_text(k), safe_text(v)] for k, v in info_rows]
        table = Table(info, colWidths=[155, 335])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#0f766e")),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
            ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f8fafc")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
        story.append(Spacer(1, 18))

    for heading, text in sections:
        story.append(Paragraph(safe_text(heading), subtitle))
        story.append(Paragraph(safe_text(text), normal))
        story.append(Spacer(1, 10))

    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "Documento gerado automaticamente pelo DataInsight Sports Analytics PRO.",
        normal
    ))

    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/teams/{id}/pdf")
def team_pdf(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = owned(db.query(Team), user).filter(Team.id == id).first()
    if not team:
        raise HTTPException(404, "Time não encontrado")

    athletes = owned(db.query(Athlete), user).filter(Athlete.team_id == id).all()
    matches = owned(db.query(Match), user).filter(Match.team_id == id).all()

    atletas_txt = "\n".join([f"- {a.name} | {a.position or 'posição não informada'}" for a in athletes]) or "Nenhum atleta cadastrado."
    jogos_txt = "\n".join([f"- {m.match_date} | {m.opponent} | {m.goals_for} x {m.goals_against}" for m in matches]) or "Nenhum jogo cadastrado."

    return make_pdf_response(
        "DataInsight Sports Analytics PRO",
        "Relatório Técnico - Time",
        [
            ("Time", team.name),
            ("Categoria", team.category),
            ("Cidade", team.city),
            ("Treinador", team.coach),
        ],
        [
            ("Observações", team.notes),
            ("Atletas do Time", atletas_txt),
            ("Jogos do Time", jogos_txt),
        ],
        f"time_{team.id}.pdf"
    )

@app.get("/api/athletes/{id}/pdf")
def athlete_pdf(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    athlete = owned(db.query(Athlete), user).filter(Athlete.id == id).first()
    if not athlete:
        raise HTTPException(404, "Atleta não encontrado")

    team = owned(db.query(Team), user).filter(Team.id == athlete.team_id).first()
    events = owned(db.query(ScoutEvent), user).filter(ScoutEvent.athlete_id == id).all()

    by_event = {}
    for e in events:
        by_event[e.event_type] = by_event.get(e.event_type, 0) + 1
    resumo_eventos = "\n".join([f"- {k}: {v}" for k, v in by_event.items()]) or "Nenhum evento registrado."

    return make_pdf_response(
        "DataInsight Sports Analytics PRO",
        "Relatório Técnico - Atleta",
        [
            ("Atleta", athlete.name),
            ("Time", team.name if team else "Não informado"),
            ("Posição", athlete.position),
            ("Pé dominante", athlete.dominant_foot),
            ("Idade", athlete.age),
            ("Altura", athlete.height),
            ("Peso", athlete.weight),
        ],
        [
            ("Pontos Fortes", athlete.strengths),
            ("Pontos a Melhorar", athlete.weaknesses),
            ("Resumo de Eventos de Scout", resumo_eventos),
        ],
        f"atleta_{athlete.id}.pdf"
    )

@app.get("/api/matches/{id}/pdf")
def match_pdf(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    match = owned(db.query(Match), user).filter(Match.id == id).first()
    if not match:
        raise HTTPException(404, "Jogo não encontrado")

    team = owned(db.query(Team), user).filter(Team.id == match.team_id).first()
    events = owned(db.query(ScoutEvent), user).filter(ScoutEvent.match_id == id).order_by(ScoutEvent.minute.asc()).all()
    athletes = {a.id: a.name for a in owned(db.query(Athlete), user).all()}

    eventos_txt = "\n".join([
        f"{e.minute}' - {e.event_type} | {athletes.get(e.athlete_id, 'Atleta não informado')} | {e.zone or ''} | {e.result or ''}"
        for e in events
    ]) or "Nenhum evento registrado."

    by_event = {}
    for e in events:
        by_event[e.event_type] = by_event.get(e.event_type, 0) + 1
    resumo_txt = "\n".join([f"- {k}: {v}" for k, v in by_event.items()]) or "Nenhum resumo disponível."

    return make_pdf_response(
        "DataInsight Sports Analytics PRO",
        "Relatório Técnico - Jogo",
        [
            ("Time", team.name if team else "Não informado"),
            ("Data", match.match_date),
            ("Adversário", match.opponent),
            ("Competição", match.competition),
            ("Local", match.location),
            ("Formação", match.formation),
            ("Placar", f"{match.goals_for} x {match.goals_against}"),
        ],
        [
            ("Observações", match.notes),
            ("Resumo dos Eventos", resumo_txt),
            ("Eventos da Partida", eventos_txt),
        ],
        f"jogo_{match.id}.pdf"
    )

@app.get("/api/scout/pdf")
def scout_pdf(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    events = owned(db.query(ScoutEvent), user).order_by(ScoutEvent.minute.asc()).all()
    athletes = {a.id: a.name for a in owned(db.query(Athlete), user).all()}
    matches = {m.id: f"{m.match_date} - {m.opponent}" for m in owned(db.query(Match), user).all()}

    eventos_txt = "\n".join([
        f"{e.minute}' | {matches.get(e.match_id, 'Jogo não informado')} | {athletes.get(e.athlete_id, 'Atleta não informado')} | {e.event_type} | {e.zone or ''} | {e.result or ''} | {e.notes or ''}"
        for e in events
    ]) or "Nenhum evento registrado."

    by_event = {}
    for e in events:
        by_event[e.event_type] = by_event.get(e.event_type, 0) + 1
    resumo_txt = "\n".join([f"- {k}: {v}" for k, v in by_event.items()]) or "Nenhum resumo disponível."

    return make_pdf_response(
        "DataInsight Sports Analytics PRO",
        "Relatório Técnico - Scout",
        [("Total de Eventos", len(events))],
        [
            ("Resumo por Tipo de Evento", resumo_txt),
            ("Eventos Registrados", eventos_txt),
        ],
        "scout.pdf"
    )

@app.get("/api/opponents/{id}/pdf")
def opponent_pdf(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    opponent = owned(db.query(OpponentAnalysis), user).filter(OpponentAnalysis.id == id).first()
    if not opponent:
        raise HTTPException(404, "Análise de adversário não encontrada")

    return make_pdf_response(
        "DataInsight Sports Analytics PRO",
        "Relatório Técnico - Análise do Adversário",
        [
            ("Adversário", opponent.opponent),
            ("Formação Base", opponent.base_formation),
            ("Lado Forte", opponent.attack_side),
        ],
        [
            ("Jogadores Destaque", opponent.strong_players),
            ("Pontos Fortes", opponent.strengths),
            ("Pontos Fracos", opponent.weaknesses),
            ("Bola Parada Ofensiva", opponent.set_pieces_attack),
            ("Bola Parada Defensiva", opponent.set_pieces_defense),
            ("Como Faz Gols", opponent.how_scores),
            ("Como Sofre Gols", opponent.how_concedes),
        ],
        f"adversario_{opponent.id}.pdf"
    )

@app.get("/api/gameplans/{id}/pdf")
def gameplan_pdf(id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = owned(db.query(GamePlan), user).filter(GamePlan.id == id).first()
    if not plan:
        raise HTTPException(404, "Plano de jogo não encontrado")

    return make_pdf_response(
        "DataInsight Sports Analytics PRO",
        "Relatório Técnico - Plano de Jogo",
        [
            ("Adversário", plan.opponent),
            ("Formação Recomendada", plan.recommended_formation),
        ],
        [
            ("Estratégia Defensiva", plan.defensive_strategy),
            ("Estratégia Ofensiva", plan.offensive_strategy),
            ("Marcação Individual", plan.individual_marking),
            ("Plano de Bola Parada", plan.set_piece_plan),
            ("Substituições Previstas", plan.substitutions),
            ("Sugestão Inteligente", plan.ai_suggestion),
        ],
        f"plano_jogo_{plan.id}.pdf"
    )

# DASHBOARD
@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    matches = owned(db.query(Match), user).all()
    athletes = owned(db.query(Athlete), user).all()
    events = owned(db.query(ScoutEvent), user).all()

    total = len(matches)
    wins = sum(1 for m in matches if m.goals_for > m.goals_against)
    draws = sum(1 for m in matches if m.goals_for == m.goals_against)
    losses = total - wins - draws

    gf = sum(m.goals_for for m in matches)
    ga = sum(m.goals_against for m in matches)
    saldo = gf - ga

    aproveitamento = round(((wins * 3 + draws) / (total * 3)) * 100, 1) if total > 0 else 0
    media_gols_pro = round(gf / total, 2) if total > 0 else 0
    media_gols_contra = round(ga / total, 2) if total > 0 else 0

    by_event = {}
    by_zone = {}
    by_athlete = {}

    for e in events:
        by_event[e.event_type] = by_event.get(e.event_type, 0) + 1

        if e.zone:
            by_zone[e.zone] = by_zone.get(e.zone, 0) + 1

        if e.athlete_id:
            by_athlete[e.athlete_id] = by_athlete.get(e.athlete_id, 0) + 1

    athlete_names = {a.id: a.name for a in athletes}

    ranking_athletes = [
        {
            "athlete_id": athlete_id,
            "name": athlete_names.get(athlete_id, "Atleta não identificado"),
            "events": total_events
        }
        for athlete_id, total_events in by_athlete.items()
    ]

    ranking_athletes = sorted(
        ranking_athletes,
        key=lambda x: x["events"],
        reverse=True
    )[:5]

    last_matches = [
        {
            "date": str(m.match_date),
            "opponent": m.opponent,
            "score": f"{m.goals_for} x {m.goals_against}",
            "formation": m.formation or "",
            "competition": m.competition or "",
            "location": m.location or ""
        }
        for m in matches[:5]
    ]

    return {
        "teams": owned(db.query(Team), user).count(),
        "athletes": len(athletes),
        "matches": total,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goals_for": gf,
        "goals_against": ga,
        "saldo": saldo,
        "aproveitamento": aproveitamento,
        "media_gols_pro": media_gols_pro,
        "media_gols_contra": media_gols_contra,
        "event_counts": by_event,
        "zone_counts": by_zone,
        "ranking_athletes": ranking_athletes,
        "last_matches": last_matches
    }
