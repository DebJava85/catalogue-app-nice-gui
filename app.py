import sqlite3
import json
from nicegui import ui

# Database Setup
conn = sqlite3.connect("catalogue.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS catalogue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        category TEXT,
        details TEXT,
        tags TEXT,
        reminder TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

CATEGORY_INFO = {
    "URL": {"icon": "🌐", "color": "blue"},
    "Property": {"icon": "🏠", "color": "green"},
    "Other": {"icon": "📁", "color": "gray"},
}

dark_mode = False
selected_category = "All"
view_mode = "Table"

# Fetch entries
def get_entries(order_by="created_at DESC"):
    query = "SELECT * FROM catalogue"
    conditions = []
    params = []

    if selected_category != "All":
        conditions.append("category=?")
        params.append(selected_category)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += f" ORDER BY {order_by}"
    cursor.execute(query, params)
    return cursor.fetchall()

# Create new entry
def add_entry(title, category, details, tags, reminder):
    cursor.execute("INSERT INTO catalogue (title, category, details, tags, reminder) VALUES (?, ?, ?, ?, ?)",
                   (title, category, details, json.dumps(tags), reminder))
    conn.commit()
    refresh_catalogue()

# Update entry
def update_entry(entry_id, field, value):
    if field == "tags":
        value = json.dumps(value)
    cursor.execute(f"UPDATE catalogue SET {field}=? WHERE id=?", (value, entry_id))
    conn.commit()
    refresh_catalogue()

# Delete entry
def delete_entry(entry_id):
    cursor.execute("DELETE FROM catalogue WHERE id=?", (entry_id,))
    conn.commit()
    refresh_catalogue()

# Refresh UI
def refresh_catalogue():
    table_container.clear()
    entries = get_entries()

    with table_container:
        if view_mode == "Table":
            with ui.table(columns=["Title", "Category", "Details", "Tags", "Reminder", "Actions"], rows=[]).classes("w-full"):
                for entry in entries:
                    entry_id, title, category, details, tags_json, reminder, created_at = entry
                    tags = json.loads(tags_json) if tags_json else []

                    with ui.table_row():
                        ui.input(value=title, on_change=lambda value, e_id=entry_id: update_entry(e_id, "title", value))
                        ui.select(["URL", "Property", "Other"], value=category, on_change=lambda value, e_id=entry_id: update_entry(e_id, "category", value))
                        ui.textarea(value=details, on_change=lambda value, e_id=entry_id: update_entry(e_id, "details", value))
                        ui.multiselect(["Important", "Work", "Personal", "Reference"], value=tags, on_change=lambda value, e_id=entry_id: update_entry(e_id, "tags", value))
                        ui.input(type="datetime-local", value=reminder, on_change=lambda value, e_id=entry_id: update_entry(e_id, "reminder", value))
                        ui.button("🗑️", on_click=lambda e_id=entry_id: delete_entry(e_id), color="red")

# UI Layout
with ui.column().classes('w-full max-w-3xl mx-auto'):
    with ui.row():
        ui.label("📖 My Development Catalogue").classes('text-2xl font-bold mt-4')
        ui.switch("🌙 Dark Mode", on_change=lambda: (ui.colors(background="black" if dark_mode else "white"), refresh_catalogue()))

    with ui.row():
        ui.select(["Table", "Timeline"], value="Table", on_change=lambda value: refresh_catalogue())
        ui.select(["All", "URL", "Property", "Other"], value="All", on_change=lambda value: refresh_catalogue())

    # Create Button - Opens a modal popup
    def open_create_modal():
        with ui.dialog() as create_dialog, ui.card():
            ui.label("➕ Add New Entry").classes("text-xl font-bold")
            new_title = ui.input("Title").classes("w-full")
            new_category = ui.select(["URL", "Property", "Other"], value="URL").classes("w-full")
            new_details = ui.textarea("Details").classes("w-full")
            new_tags = ui.multiselect(["Important", "Work", "Personal", "Reference"], value=[]).classes("w-full")
            new_reminder = ui.input("Reminder (optional)", type="datetime-local").classes("w-full")
            
            def save_new_entry():
                add_entry(new_title.value, new_category.value, new_details.value, new_tags.value, new_reminder.value)
                create_dialog.close()

            ui.button("Save", on_click=save_new_entry, color="green").classes("mt-4")
            ui.button("Cancel", on_click=create_dialog.close).classes("mt-4")

        create_dialog.open()

    ui.button("➕ Add New", on_click=open_create_modal, color="blue").classes("mt-4")

    table_container = ui.column().classes('mt-4')

refresh_catalogue()
ui.run()