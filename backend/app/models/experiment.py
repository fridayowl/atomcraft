import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    name = Column(String(255))
    experiment_type = Column(String(100))
    description = Column(Text)
    status = Column(String(50), default="planned")
    synthesis_method = Column(String(100))
    synthesis_conditions = Column(JSON, default=dict)
    precursor_materials = Column(JSON, default=list)
    equipment_used = Column(JSON, default=list)
    successful = Column(Boolean, nullable=True)
    notes = Column(Text)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    material = relationship("Material", back_populates="experiments")
    steps = relationship("ExperimentStep", back_populates="experiment", cascade="all, delete-orphan")
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")


class ExperimentStep(Base):
    __tablename__ = "experiment_steps"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    step_number = Column(Integer)
    step_type = Column(String(100))
    description = Column(Text)
    duration_minutes = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    atmosphere = Column(String(100))
    notes = Column(Text)
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    experiment = relationship("Experiment", back_populates="steps")


class ExperimentResult(Base):
    __tablename__ = "experiment_results"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    result_type = Column(String(100))
    value = Column(Float, nullable=True)
    unit = Column(String(50), nullable=True)
    characterization_method = Column(String(100))
    file_path = Column(String(500), nullable=True)
    data_json = Column(JSON, nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    experiment = relationship("Experiment", back_populates="results")
