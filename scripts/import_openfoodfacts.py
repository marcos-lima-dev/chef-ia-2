import requests
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.infrastructure.database.base import SessionLocal
from app.infrastructure.database.models_catalog import IngredientCatalog, IngredientAlias, IngredientCategory, IngredientSource

def fetch_openfoodfacts_products(category="foods", page=1):
    url = f"https://world.openfoodfacts.org/api/v2/search?categories_tags=en:{category}&page_size=1000&page={page}"
    headers = {"User-Agent": "ChefeIA/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Erro ao buscar Open Food Facts: {e}")
        return None

def import_openfoodfacts():
    db = SessionLocal()
    try:
        # Busca por várias categorias
        categories = ["vegetables", "fruits", "meat", "fish", "dairy", "spices", "herbs", "legumes", "cereals"]
        total_count = 0
        
        for cat in categories:
            print(f"   Buscando categoria: {cat}...")
            data = fetch_openfoodfacts_products(cat)
            if not data or "products" not in data:
                continue
            
            for product in data["products"]:
                name = product.get("product_name_pt") or product.get("product_name", "")
                if not name:
                    continue
                name = name.strip().lower()
                
                # Pega categoria do produto
                categories_tags = product.get("categories_tags", [])
                category_name = None
                for tag in categories_tags:
                    if tag.startswith("en:"):
                        category_name = tag.replace("en:", "").replace("-", " ").strip()
                        break
                
                category = None
                if category_name:
                    category = db.query(IngredientCategory).filter(IngredientCategory.name == category_name).first()
                    if not category:
                        category = IngredientCategory(name=category_name)
                        db.add(category)
                        db.flush()
                
                existing = db.query(IngredientCatalog).filter(IngredientCatalog.canonical_name == name).first()
                if existing:
                    continue
                
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
                
                if product.get("other_names"):
                    for alias in product["other_names"].split(","):
                        alias = alias.strip().lower()
                        if alias and alias != name:
                            db.add(IngredientAlias(ingredient_id=ingredient.id, alias=alias, source="openfoodfacts"))
                
                db.add(IngredientSource(
                    ingredient_id=ingredient.id,
                    source="openfoodfacts",
                    external_id=product.get("code"),
                    imported_at=datetime.now()
                ))
                total_count += 1
                if total_count % 100 == 0:
                    print(f"   Processados {total_count} produtos...")
            
            print(f"   Categoria {cat}: {len(data['products'])} produtos processados.")
        
        db.commit()
        print(f"✅ Open Food Facts importado com sucesso! {total_count} produtos adicionados.")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao importar Open Food Facts: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    import_openfoodfacts()