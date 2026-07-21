import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.import_wikidata import import_wikidata
from scripts.import_openfoodfacts import import_openfoodfacts

def main():
    print("🚀 Iniciando ETL do catálogo de ingredientes...")
    print("1. Importando Wikidata...")
    import_wikidata()
    print("2. Importando Open Food Facts...")
    import_openfoodfacts()
    print("✅ ETL concluído!")

if __name__ == "__main__":
    main()