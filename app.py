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

        elif view_mode == "Timeline":
            with ui.timeline():
                for entry in entries:
                    entry_id, title, category, details, tags_json, reminder, created_at = entry
                    tags = json.loads(tags_json) if tags_json else []
                    category_info = CATEGORY_INFO.get(category, {"icon": "📁", "color": "gray"})

                    with ui.timeline_event():
                        ui.icon(category_info["icon"]).classes(f"text-{category_info['color']}-500")
                        ui.label(f"**{title}** - {category}").classes("text-lg font-bold")
                        ui.label(details).classes("text-sm italic text-gray-600")
                        ui.label(f"📅 {created_at}").classes("text-xs text-gray-500")
                        if tags:
                            ui.label("Tags: " + ", ".join(tags)).classes("text-xs text-gray-400")
                        if reminder:
                            ui.label(f"⏰ Reminder: {reminder}").classes("text-xs text-red-500")

# Toggle View Mode
def toggle_view_mode(value):
    global view_mode
    view_mode = value
    refresh_catalogue()

# UI Layout
with ui.column().classes('w-full max-w-3xl mx-auto'):
    with ui.row():
        ui.label("📖 My Development Catalogue").classes('text-2xl font-bold mt-4')
        ui.switch("🌙 Dark Mode", on_change=lambda: (ui.colors(background="black" if dark_mode else "white"), refresh_catalogue()))

    with ui.row():
        ui.select(["Table", "Timeline"], value="Table", on_change=toggle_view_mode)
        ui.select(["All", "URL", "Property", "Other"], value="All", on_change=lambda value: update_entry("category", value))

    table_container = ui.column().classes('mt-4')

refresh_catalogue()
ui.run()