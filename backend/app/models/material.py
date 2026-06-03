import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    formula = Column(String(255), index=True)
    formula_html = Column(String(512))
    space_group = Column(String(50))
    crystal_system = Column(String(50))
    lattice_a = Column(Float)
    lattice_b = Column(Float)
    lattice_c = Column(Float)
    lattice_alpha = Column(Float)
    lattice_beta = Column(Float)
    lattice_gamma = Column(Float)
    volume = Column(Float)
    density = Column(Float)
    cif_data = Column(Text)
    mp_id = Column(String(50), index=True)
    icsd_id = Column(String(50))
    tags = Column(JSON, default=list)
    public = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    properties = relationship("Property", back_populates="material", cascade="all, delete-orphan")
    compositions = relationship("Composition", back_populates="material", cascade="all, delete-orphan")
    phases = relationship("Phase", back_populates="material", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="material", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="material", cascade="all, delete-orphan")


class Composition(Base):
    __tablename__ = "compositions"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    element = Column(String(10), index=True)
    amount = Column(Float)
    atomic_fraction = Column(Float)

    material = relationship("Material", back_populates="compositions")


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    property_type = Column(String(100), index=True)
    value = Column(Float)
    unit = Column(String(50))
    source = Column(String(100))
    confidence = Column(Float, default=0.0)
    method = Column(String(100))

    material = relationship("Material", back_populates="properties")


class Phase(Base):
    __tablename__ = "phases"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    phase_name = Column(String(100))
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    pressure_min = Column(Float, nullable=True)
    pressure_max = Column(Float, nullable=True)
    stability = Column(String(50))
    notes = Column(Text)

    material = relationship("Material", back_populates="phases")
