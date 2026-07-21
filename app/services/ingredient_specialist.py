import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from rapidfuzz import fuzz, process
from datetime import datetime
from langchain_core.messages import SystemMessage, HumanMessage

from app.infrastructure.database.models_catalog import (
    IngredientCatalog,
    IngredientAlias,
    UnknownTerm,
)
from app.domain.models.ingredient import IngredientEntity
from app.domain.models.ingredient_resolution import IngredientResolution
from app.core.llm_provider import get_llm


class IngredientSpecialist:
    # Lista de termos claramente não alimentícios
    REJECTED_TERMS = {
        "martelo", "prego", "parafuso", "chave", "alicate", "furadeira",
        "serra", "tijolo", "cimento", "areia", "pedra", "terra", "plástico",
        "pneu", "martelo", "óleo queimado"
    }

    def __init__(self, db: Session):
        self.db = db
        self._cache = {}

    def resolve(self, terms: List[str]) -> List[IngredientResolution]:
        results = []
        for term in terms:
            result = self._resolve_single(term.strip().lower())
            results.append(result)
        return results

    def _resolve_single(self, term: str) -> IngredientResolution:
        if term in self._cache:
            return self._cache[term]

        # 0. Lista negra (rejeição imediata)
        if term in self.REJECTED_TERMS:
            result = IngredientResolution(
                original_input=term,
                normalized_input=None,
                entity=None,
                resolution="rejected",
                match_confidence=0.0,
                reason="not_food",
                suggestions=[],
                action="block",
            )
            self._cache[term] = result
            return result

        # 1. Busca exata
        ingredient = self._lookup_exact(term)
        if ingredient:
            result = IngredientResolution(
                original_input=term,
                normalized_input=ingredient.canonical_name,
                entity=self._to_entity(ingredient),
                resolution="resolved",
                match_confidence=1.0,
                reason="exact_match",
                suggestions=[],
                action="continue",
            )
            self._cache[term] = result
            return result

        # 2. Busca fuzzy com limiares mais altos
        fuzzy_result = self._lookup_fuzzy(term)
        if fuzzy_result:
            score = fuzzy_result["score"] / 100
            if score >= 0.95:
                result = IngredientResolution(
                    original_input=term,
                    normalized_input=fuzzy_result["ingredient"].canonical_name,
                    entity=self._to_entity(fuzzy_result["ingredient"]),
                    resolution="resolved",
                    match_confidence=score,
                    reason="fuzzy_match_high",
                    suggestions=[],
                    action="continue",
                )
                self._cache[term] = result
                return result
            elif score >= 0.85:
                result = IngredientResolution(
                    original_input=term,
                    normalized_input=fuzzy_result["ingredient"].canonical_name,
                    entity=self._to_entity(fuzzy_result["ingredient"]),
                    resolution="suggested",
                    match_confidence=score,
                    reason="fuzzy_match_medium",
                    suggestions=[fuzzy_result["ingredient"].canonical_name],
                    action="needs_confirmation",
                )
                self._cache[term] = result
                self._register_unknown(term, resolution="suggested", confidence=score, suggestion=fuzzy_result["ingredient"].canonical_name)
                return result
            # Se score < 0.85, ignora o fuzzy e vai para LLM (não usa a sugestão)

        # 3. Fallback via LLM com prompt específico (sem influência do fuzzy)
        fallback_result = self._classify_with_llm(term)

        if fallback_result["is_food"]:
            suggestion = fallback_result.get("suggestion")
            if suggestion:
                # Tenta encontrar a sugestão no catálogo
                suggested_ingredient = self._lookup_exact(suggestion) or self._lookup_fuzzy(suggestion)
                if suggested_ingredient:
                    ing_obj = suggested_ingredient if isinstance(suggested_ingredient, IngredientCatalog) else suggested_ingredient.get("ingredient")
                    if ing_obj:
                        result = IngredientResolution(
                            original_input=term,
                            normalized_input=ing_obj.canonical_name,
                            entity=self._to_entity(ing_obj),
                            resolution="suggested",
                            match_confidence=0.7,
                            reason="llm_fallback_suggested",
                            suggestions=[ing_obj.canonical_name],
                            action="needs_confirmation",
                        )
                        self._cache[term] = result
                        self._register_unknown(term, resolution="suggested", confidence=0.7, suggestion=ing_obj.canonical_name)
                        return result

            # Se não há sugestão, registra como unknown
            result = IngredientResolution(
                original_input=term,
                normalized_input=None,
                entity=None,
                resolution="unknown",
                match_confidence=0.0,
                reason="llm_fallback_unknown",
                suggestions=[],
                action="needs_confirmation",
            )
            self._cache[term] = result
            self._register_unknown(term, resolution="unknown", confidence=0.0)
            return result
        else:
            # LLM disse que não é alimento → rejected
            result = IngredientResolution(
                original_input=term,
                normalized_input=None,
                entity=None,
                resolution="rejected",
                match_confidence=0.0,
                reason="llm_fallback_rejected",
                suggestions=[],
                action="block",
            )
            self._cache[term] = result
            self._register_unknown(term, resolution="rejected", confidence=0.0)
            return result

    def _classify_with_llm(self, term: str) -> Dict[str, Any]:
        """
        Usa um prompt específico para classificar se o termo é um alimento.
        Retorna:
            {
                "is_food": bool,
                "suggestion": Optional[str]  # nome mais comum, se aplicável
            }
        """
        llm = get_llm()
        system_prompt = """
        Você é um classificador especializado em alimentos.
        Sua tarefa é determinar se um termo digitado pelo usuário é um alimento comestível.
        Responda APENAS no formato JSON:
        {
            "is_food": true/false,
            "suggestion": "nome mais comum do alimento" ou null
        }
        """
        user_prompt = f"Termo: '{term}'"

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        content = response.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                return {
                    "is_food": data.get("is_food", False),
                    "suggestion": data.get("suggestion")
                }
            except json.JSONDecodeError:
                pass

        return {"is_food": False, "suggestion": None}

    def _lookup_exact(self, term: str) -> Optional[IngredientCatalog]:
        ing = self.db.query(IngredientCatalog).filter(
            IngredientCatalog.canonical_name == term
        ).first()
        if ing:
            return ing

        alias = self.db.query(IngredientAlias).filter(
            IngredientAlias.alias == term
        ).first()
        if alias:
            return alias.ingredient

        return None

    def _lookup_fuzzy(self, term: str) -> Optional[Dict]:
        candidates = []
        for ing in self.db.query(IngredientCatalog).all():
            candidates.append((ing.canonical_name, ing))
            for alias in ing.aliases:
                candidates.append((alias.alias, ing))

        if not candidates:
            return None

        choices = [c[0] for c in candidates]
        result = process.extractOne(term, choices, scorer=fuzz.WRatio)
        if result:
            best_match, score, idx = result
            return {"ingredient": candidates[idx][1], "score": score}

        return None

    def _register_unknown(self, term: str, resolution: str = "unknown", confidence: float = 0.0, suggestion: Optional[str] = None):
        existing = self.db.query(UnknownTerm).filter(
            UnknownTerm.term == term
        ).first()
        if existing:
            existing.frequency += 1
            existing.last_seen = datetime.now()
            # Atualiza campos extras se existirem
            if hasattr(existing, 'resolution'):
                existing.resolution = resolution
            if hasattr(existing, 'confidence'):
                existing.confidence = confidence
            if hasattr(existing, 'suggestion'):
                existing.suggestion = suggestion
        else:
            unknown = UnknownTerm(
                term=term,
                frequency=1,
                first_seen=datetime.now(),
                last_seen=datetime.now(),
                status="pending",
            )
            self.db.add(unknown)
        self.db.commit()

    def _to_entity(self, ingredient: IngredientCatalog) -> IngredientEntity:
        return IngredientEntity(
            id=str(ingredient.id),
            canonical_name=ingredient.canonical_name,
            slug=ingredient.slug,
            category=ingredient.category.name if ingredient.category else None,
            edible=ingredient.edible,
            aliases=[a.alias for a in ingredient.aliases],
        )