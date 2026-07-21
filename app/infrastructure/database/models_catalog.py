from sqlalchemy import Column, String, DateTime, Integer, JSON, Boolean, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.infrastructure.database.base import Base


class IngredientCategory(Base):
    __tablename__ = "ingredient_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("ingredient_categories.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    parent = relationship("IngredientCategory", remote_side=[id])
    ingredients = relationship("IngredientCatalog", back_populates="category")


class IngredientCatalog(Base):
    __tablename__ = "ingredient_catalog"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name = Column(String(200), unique=True, nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("ingredient_categories.id"))
    edible = Column(Boolean, default=True)
    status = Column(String(20), default="active")  # active | deprecated | draft
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    category = relationship("IngredientCategory", back_populates="ingredients")
    aliases = relationship("IngredientAlias", back_populates="ingredient")
    embeddings = relationship("IngredientEmbedding", back_populates="ingredient", uselist=False)
    extra_metadata = relationship("IngredientExtraMetadata", back_populates="ingredient", uselist=False)
    sources = relationship("IngredientSource", back_populates="ingredient")


class IngredientAlias(Base):
    __tablename__ = "ingredient_aliases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredient_catalog.id"), nullable=False)
    alias = Column(String(200), nullable=False)
    language = Column(String(10), default="pt")
    is_primary = Column(Boolean, default=False)
    source = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

    ingredient = relationship("IngredientCatalog", back_populates="aliases")


class IngredientEmbedding(Base):
    __tablename__ = "ingredient_embeddings"

    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredient_catalog.id"), primary_key=True)
    embedding = Column(JSON, nullable=False)
    model = Column(String(100), default="all-MiniLM-L6-v2")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    ingredient = relationship("IngredientCatalog", back_populates="embeddings")


class IngredientExtraMetadata(Base):
    __tablename__ = "ingredient_extra_metadata"

    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredient_catalog.id"), primary_key=True)
    nutritional_info = Column(JSON, default={})
    seasonality = Column(JSON, default=[])
    custom_properties = Column(JSON, default={})
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    ingredient = relationship("IngredientCatalog", back_populates="extra_metadata")


class IngredientSource(Base):
    __tablename__ = "ingredient_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredient_catalog.id"), nullable=False)
    source = Column(String(50), nullable=False)
    external_id = Column(String(200))
    version = Column(String(50))
    imported_at = Column(DateTime, default=datetime.now)

    ingredient = relationship("IngredientCatalog", back_populates="sources")


class UnknownTerm(Base):
    __tablename__ = "unknown_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term = Column(String(200), nullable=False)
    frequency = Column(Integer, default=1)
    first_seen = Column(DateTime, default=datetime.now)
    last_seen = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="pending")  # pending | approved | rejected
    reviewed_by = Column(String(100))
    ingredient_id = Column(UUID(as_uuid=True), ForeignKey("ingredient_catalog.id"))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 🔥 NOVOS CAMPOS para enriquecer o registro de unknown
    resolution = Column(String(20), nullable=True)    
    confidence = Column(Float, nullable=True)         
    suggestion = Column(String(200), nullable=True)  