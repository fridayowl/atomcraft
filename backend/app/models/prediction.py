import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("materials.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    prediction_type = Column(String(100), index=True)
    model_name = Column(String(100))
    model_version = Column(String(50))
    predicted_value = Column(Float)
    predicted_value_max = Column(Float, nullable=True)
    unit = Column(String(50))
    confidence = Column(Float, default=0.0)
    feature_importance = Column(JSON, nullable=True)
    input_descriptors = Column(JSON, nullable=True)
    validated = Column(Boolean, default=False)
    experimental_value = Column(Float, nullable=True)
    error = Column(Float, nullable=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    material = relationship("Material", back_populates="predictions")
    user = relationship("User")


class PredictionJob(Base):
    __tablename__ = "prediction_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_type = Column(String(100))
    input_data = Column(JSON)
    status = Column(String(50), default="queued")
    progress = Column(Float, default=0.0)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    dft_cost = Column(Float, nullable=True)
    compute_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
