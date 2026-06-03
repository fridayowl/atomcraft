import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    full_name = Column(String(255))
    affiliation = Column(String(255))
    title = Column(String(255))
    orcid = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    api_key = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    team_memberships = relationship("TeamMember", back_populates="user")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255))
    description = Column(String(500))
    owner_id = Column(Integer, ForeignKey("users.id"))
    max_members = Column(Integer, default=10)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String(50), default="member")
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


