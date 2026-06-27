from datetime import date
from pydantic import BaseModel
from typing import Optional

class RegisterIn(BaseModel):
    name: str
    email: str
    password: str

class LoginIn(BaseModel):
    email: str
    password: str

class TeamIn(BaseModel):
    name: str
    category: str = "Livre"
    city: str = ""
    coach: str = ""
    logo_url: str = ""
    notes: str = ""

class AthleteIn(BaseModel):
    team_id: int
    name: str
    position: str = ""
    dominant_foot: str = ""
    age: int = 0
    height: float = 0
    weight: float = 0
    photo_url: str = ""
    strengths: str = ""
    weaknesses: str = ""

class MatchIn(BaseModel):
    team_id: int
    match_date: date
    opponent: str
    location: str = ""
    competition: str = ""
    formation: str = "4-4-2"
    goals_for: int = 0
    goals_against: int = 0
    video_url: str = ""
    notes: str = ""

class ScoutEventIn(BaseModel):
    match_id: int
    athlete_id: Optional[int] = None
    minute: int = 0
    event_type: str
    zone: str = ""
    result: str = ""
    notes: str = ""

class OpponentIn(BaseModel):
    opponent: str
    base_formation: str = ""
    attack_side: str = ""
    strong_players: str = ""
    strengths: str = ""
    weaknesses: str = ""
    set_pieces_attack: str = ""
    set_pieces_defense: str = ""
    how_scores: str = ""
    how_concedes: str = ""

class GamePlanIn(BaseModel):
    opponent: str
    recommended_formation: str = ""
    defensive_strategy: str = ""
    offensive_strategy: str = ""
    individual_marking: str = ""
    set_piece_plan: str = ""
    substitutions: str = ""
