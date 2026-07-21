import requests
import uuid
import time
from datetime import datetime
from sqlalchemy.orm import Session
from app.infrastructure.database.base import SessionLocal
from app.infrastructure.database.models_catalog import IngredientCatalog, IngredientAlias, IngredientCategory, IngredientSource

SPARQL_QUERY = """
SELECT DISTINCT ?item ?itemLabel ?aliases ?categoryLabel WHERE {
  ?item wdt:P31 wd:Q2095.
  ?item rdfs:label ?itemLabel.
  FILTER(LANG(?itemLabel) = "pt")
  OPTIONAL { ?item skos:altLabel ?aliases. FILTER(LANG(?aliases) = "pt") }
  OPTIONAL {
    ?item wdt:P279 ?category.
    ?category rdfs:label ?categoryLabel.
    FILTER(LANG(?categoryLabel) = "pt")
  }
}
LIMIT 5000
"""

def import_wikidata():
    url = "https://query.wikidata.org/sparql"
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "ChefeIA/1.0 (https://github.com/marcos-lima-dev/chef-ia-2)"
    }
    params = {"query": SPARQL_QUERY, "format": "json"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        print("Resposta:", response.text[:200] if response else "Sem resposta")
        return

    if "results" not in data or "bindings" not in data["results"]:
        print("⚠️ Nenhum resultado encontrado. Verifique a query.")
        print("Resposta (primeiros 200 caracteres):", response.text[:200])
        return

    db = SessionLocal()
    try:
        count = 0
        for binding in data["results"]["bindings"]:
            # Extrai valores com segurança
            if "itemLabel" not in binding:
                continue
            name = binding["itemLabel"]["value"].strip().lower()
            
            aliases = []
            if "aliases" in binding and "value" in binding["aliases"]:
                # pode ser string ou lista
                alias_val = binding["aliases"]["value"]
                if isinstance(alias_val, str):
                    aliases = [alias_val.strip().lower()]
                elif isinstance(alias_val, list):
                    aliases = [a.strip().lower() for a in alias_val if a]
                else:
                    aliases = []

            category_name = ""
            if "categoryLabel" in binding and "value" in binding["categoryLabel"]:
                category_name = binding["categoryLabel"]["value"].strip().lower()

            # Busca ou cria categoria
            category = None
            if category_name:
                category = db.query(IngredientCategory).filter(IngredientCategory.name == category_name).first()
                if not category:
                    category = IngredientCategory(name=category_name)
                    db.add(category)
                    db.flush()

            # Verifica duplicata
            existing = db.query(IngredientCatalog).filter(IngredientCatalog.canonical_name == name).first()
            if existing:
                for alias in aliases:
                    if not db.query(IngredientAlias).filter(
                        IngredientAlias.alias == alias,
                        IngredientAlias.ingredient_id == existing.id
                    ).first():
                        db.add(IngredientAlias(ingredient_id=existing.id, alias=alias, source="wikidata"))
                continue

            # Cria ingrediente
            ingredient = IngredientCatalog(
                id=uuid.uuid4(),
                canonical_name=name,
                slug=name.replace(" ", "-"),
                category_id=category.id if category else None,
                edible=True,
                status="active",
            )
            db.add(ingredient)
            db.flush()

            for alias in aliases:
                db.add(IngredientAlias(ingredient_id=ingredient.id, alias=alias, source="wikidata"))

            # Obtém external_id
            external_id = ""
            if "item" in binding and "value" in binding["item"]:
                external_id = binding["item"]["value"].split("/")[-1]

            db.add(IngredientSource(
                ingredient_id=ingredient.id,
                source="wikidata",
                external_id=external_id,
                imported_at=datetime.now()
            ))
            count += 1
            if count % 100 == 0:
                print(f"   Processados {count} ingredientes...")

        db.commit()
        print(f"✅ Wikidata importado com sucesso! {count} ingredientes adicionados.")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao importar Wikidata: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import_wikidata()