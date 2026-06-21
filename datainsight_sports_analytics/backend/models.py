from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), default="gestor")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(160), nullable=False)
    category = Column(String(80), default="Livre")
    city = Column(String(120), default="")
    coach = Column(String(120), default="")
    notes = Column(Text, default="")

class Athlete(Base):
    __tablename__ = "athletes"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    name = Column(String(160), nullable=False)
    position = Column(String(60), default="")
    dominant_foot = Column(String(20), default="")
    age = Column(Integer, default=0)
    height = Column(Float, default=0)
    weight = Column(Float, default=0)
    strengths = Column(Text, default="")
    weaknesses = Column(Text, default="")

class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    match_date = Column(Date, nullable=False)
    opponent = Column(String(160), nullable=False)
    location = Column(String(120), default="")
    competition = Column(String(120), default="")
    formation = Column(String(40), default="4-4-2")
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    notes = Column(Text, default="")

class ScoutEvent(Base):
    __tablename__ = "scout_events"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=True)
    minute = Column(Integer, default=0)
    event_type = Column(String(80), nullable=False)
    zone = Column(String(80), default="")
    result = Column(String(80), default="")
    notes = Column(Text, default="")

class OpponentAnalysis(Base):
    __tablename__ = "opponent_analyses"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opponent = Column(String(160), nullable=False)
    base_formation = Column(String(40), default="")
    attack_side = Column(String(40), default="")
    strong_players = Column(Text, default="")
    strengths = Column(Text, default="")
    weaknesses = Column(Text, default="")
    set_pieces_attack = Column(Text, default="")
    set_pieces_defense = Column(Text, default="")
    how_scores = Column(Text, default="")
    how_concedes = Column(Text, default="")

class GamePlan(Base):
    __tablename__ = "game_plans"
    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    opponent = Column(String(160), nullable=False)
    recommended_formation = Column(String(40), default="")
    defensive_strategy = Column(Text, default="")
    offensive_strategy = Column(Text, default="")
    individual_marking = Column(Text, default="")
    set_piece_plan = Column(Text, default="")
    substitutions = Column(Text, default="")
    ai_suggestion = Column(Text, default="")
