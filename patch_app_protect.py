import os
import re

file_path = r'f:\Cognify\app.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix upgrade_question_bank_schema()
content = content.replace("upgrade_question_bank_schema()", "")

# Fix upgrade_semantic_schema()
content = content.replace("upgrade_semantic_schema()", "")

# Add them to the bottom
bottom = """
if __name__ == "__main__":
    upgrade_question_bank_schema()
    upgrade_semantic_schema()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))"""

content = content.replace("""if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))""", bottom)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("app.py protected.")
