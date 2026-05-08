import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from tkcalendar import DateEntry

DB_FILE = "diary.db"
selected_id = None


def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS diary_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                diary_date TEXT NOT NULL,
                breakfast TEXT,
                lunch TEXT,
                dinner TEXT,
                content TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def get_conn():
    return sqlite3.connect(DB_FILE)


def clear_form():
    global selected_id
    selected_id = None
    date_entry.set_date(datetime.today())
    breakfast_entry.delete(0, tk.END)
    lunch_entry.delete(0, tk.END)
    dinner_entry.delete(0, tk.END)
    content_text.delete("1.0", tk.END)


def save_entry():
    date_str = date_entry.get_date().strftime("%Y-%m-%d")

    data = (
        date_str,
        breakfast_entry.get().strip(),
        lunch_entry.get().strip(),
        dinner_entry.get().strip(),
        content_text.get("1.0", tk.END).strip()
    )

    with get_conn() as conn:
        conn.execute("""
            INSERT INTO diary_entries
            (diary_date, breakfast, lunch, dinner, content)
            VALUES (?, ?, ?, ?, ?)
        """, data)
        conn.commit()

    messagebox.showinfo("保存完了", "日記を保存しました")
    clear_form()
    load_entries()


def update_entry():
    global selected_id

    if selected_id is None:
        messagebox.showwarning("未選択", "更新する日記を一覧から選択してください")
        return

    date_str = date_entry.get_date().strftime("%Y-%m-%d")

    data = (
        date_str,
        breakfast_entry.get().strip(),
        lunch_entry.get().strip(),
        dinner_entry.get().strip(),
        content_text.get("1.0", tk.END).strip(),
        selected_id
    )

    with get_conn() as conn:
        conn.execute("""
            UPDATE diary_entries
            SET diary_date = ?,
                breakfast = ?,
                lunch = ?,
                dinner = ?,
                content = ?
            WHERE id = ?
        """, data)
        conn.commit()

    messagebox.showinfo("更新完了", "日記を更新しました")
    clear_form()
    load_entries()


def delete_entry():
    global selected_id

    if selected_id is None:
        messagebox.showwarning("未選択", "削除する日記を一覧から選択してください")
        return

    if not messagebox.askyesno("削除確認", "選択した日記を削除しますか？"):
        return

    with get_conn() as conn:
        conn.execute("DELETE FROM diary_entries WHERE id = ?", (selected_id,))
        conn.commit()

    messagebox.showinfo("削除完了", "日記を削除しました")
    clear_form()
    load_entries()


def load_entries():
    for item in tree.get_children():
        tree.delete(item)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, diary_date, breakfast, lunch, dinner
            FROM diary_entries
            ORDER BY diary_date DESC, id DESC
        """)
        rows = cur.fetchall()

    for row in rows:
        tree.insert("", tk.END, values=row)


def search_by_date():
    search_date = search_date_entry.get_date().strftime("%Y-%m-%d")

    for item in tree.get_children():
        tree.delete(item)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, diary_date, breakfast, lunch, dinner
            FROM diary_entries
            WHERE diary_date = ?
            ORDER BY id DESC
        """, (search_date,))
        rows = cur.fetchall()

    for row in rows:
        tree.insert("", tk.END, values=row)


def on_select(event):
    global selected_id

    selected = tree.focus()
    if not selected:
        return

    values = tree.item(selected, "values")
    selected_id = values[0]

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, diary_date, breakfast, lunch, dinner, content
            FROM diary_entries
            WHERE id = ?
        """, (selected_id,))
        row = cur.fetchone()

    if row:
        date_entry.set_date(row[1])

        breakfast_entry.delete(0, tk.END)
        lunch_entry.delete(0, tk.END)
        dinner_entry.delete(0, tk.END)
        content_text.delete("1.0", tk.END)

        breakfast_entry.insert(0, row[2] or "")
        lunch_entry.insert(0, row[3] or "")
        dinner_entry.insert(0, row[4] or "")
        content_text.insert("1.0", row[5] or "")


# =========================
# GUI
# =========================
root = tk.Tk()
root.title("日記帳アプリ SQLite版")
root.geometry("950x720")


input_frame = ttk.LabelFrame(root, text="日記入力・編集")
input_frame.pack(fill="x", padx=10, pady=10)


ttk.Label(input_frame, text="日付").grid(row=0, column=0, padx=5, pady=5, sticky="w")
date_entry = DateEntry(
    input_frame,
    width=18,
    date_pattern="yyyy-mm-dd"
)
date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")


ttk.Label(input_frame, text="朝ごはん").grid(row=1, column=0, padx=5, pady=5, sticky="w")
breakfast_entry = ttk.Entry(input_frame, width=60)
breakfast_entry.grid(row=1, column=1, padx=5, pady=5)


ttk.Label(input_frame, text="昼ごはん").grid(row=2, column=0, padx=5, pady=5, sticky="w")
lunch_entry = ttk.Entry(input_frame, width=60)
lunch_entry.grid(row=2, column=1, padx=5, pady=5)


ttk.Label(input_frame, text="晩ごはん").grid(row=3, column=0, padx=5, pady=5, sticky="w")
dinner_entry = ttk.Entry(input_frame, width=60)
dinner_entry.grid(row=3, column=1, padx=5, pady=5)


ttk.Label(input_frame, text="日記本文").grid(row=4, column=0, padx=5, pady=5, sticky="nw")
content_text = tk.Text(input_frame, width=75, height=6)
content_text.grid(row=4, column=1, padx=5, pady=5)


button_frame = ttk.Frame(input_frame)
button_frame.grid(row=5, column=1, sticky="e", pady=5)

ttk.Button(button_frame, text="新規保存", command=save_entry).pack(side="left", padx=5)
ttk.Button(button_frame, text="更新", command=update_entry).pack(side="left", padx=5)
ttk.Button(button_frame, text="削除", command=delete_entry).pack(side="left", padx=5)
ttk.Button(button_frame, text="クリア", command=clear_form).pack(side="left", padx=5)


search_frame = ttk.LabelFrame(root, text="日付検索")
search_frame.pack(fill="x", padx=10, pady=5)

ttk.Label(search_frame, text="検索日").pack(side="left", padx=5)

search_date_entry = DateEntry(
    search_frame,
    width=18,
    date_pattern="yyyy-mm-dd"
)
search_date_entry.pack(side="left", padx=5)

ttk.Button(search_frame, text="検索", command=search_by_date).pack(side="left", padx=5)
ttk.Button(search_frame, text="全件表示", command=load_entries).pack(side="left", padx=5)


list_frame = ttk.LabelFrame(root, text="日記一覧")
list_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("id", "date", "breakfast", "lunch", "dinner")
tree = ttk.Treeview(list_frame, columns=columns, show="headings")

tree.heading("id", text="ID")
tree.heading("date", text="日付")
tree.heading("breakfast", text="朝ごはん")
tree.heading("lunch", text="昼ごはん")
tree.heading("dinner", text="晩ごはん")

tree.column("id", width=50)
tree.column("date", width=120)
tree.column("breakfast", width=230)
tree.column("lunch", width=230)
tree.column("dinner", width=230)

tree.pack(fill="both", expand=True)
tree.bind("<<TreeviewSelect>>", on_select)


init_db()
load_entries()

root.mainloop()
