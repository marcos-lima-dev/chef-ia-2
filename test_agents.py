from app.agents.intent_analyzer import IntentAnalyzer
from app.agents.chef import Chef
from app.agents.editor import Editor
import json

print("=" * 50)
print("Teste: IntentAnalyzer")
print("=" * 50)
analyzer = IntentAnalyzer()
intentions = analyzer.analyze("Quero uma salada leve com tomate e alface, sem glúten")
print(json.dumps(intentions, indent=2, ensure_ascii=False))

print("\n" + "=" * 50)
print("Teste: Chef")
print("=" * 50)
chef = Chef()
proposal = chef.create_proposal(intentions)
print(proposal)

print("\n" + "=" * 50)
print("Teste: Editor")
print("=" * 50)
editor = Editor()
final_response = editor.format_response(proposal)
print(final_response)
