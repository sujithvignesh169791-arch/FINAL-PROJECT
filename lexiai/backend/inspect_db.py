import sqlite3

conn = sqlite3.connect('lexiai.db')
c = conn.cursor()

tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('TABLES:', tables)
for t in tables:
    count = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"Table {t}: {count} rows")

print("\n--- FINDING 'case 1.pdf' ---")
docs = c.execute("SELECT id, user_id, filename, file_type, upload_status, created_at FROM documents WHERE filename LIKE '%case%'").fetchall()
print(f"Matched docs: {len(docs)}")
for d in docs:
    print(d)
    analysis = c.execute("SELECT id, summary IS NOT NULL, risk_score, processing_method, processing_error, length(extracted_text) FROM document_analyses WHERE document_id = ?", (d[0],)).fetchone()
    print("   Analysis:", analysis)

print("\n--- ALL USERS ---")
users = c.execute("SELECT id, email, full_name, created_at FROM users").fetchall()
print(f"Total users: {len(users)}")
for u in users[:10]:
    print(u)
