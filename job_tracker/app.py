"""Tkinter desktop window for the job application tracker."""

import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, messagebox, ttk

from job_tracker.db import FIELDS, STATUSES, Tracker

DB_PATH = os.path.join(os.path.expanduser("~"), "job_applications.db")
COLUMNS = ["company", "role", "status", "applied_on", "follow_up"]


class ApplicationForm(tk.Toplevel):
    """Dialog for adding or editing one application."""

    def __init__(self, parent, on_save, initial=None):
        super().__init__(parent)
        self.title("Edit application" if initial else "Add application")
        self.resizable(False, False)
        self.on_save = on_save
        self.vars = {}

        initial = dict(initial) if initial else {
            "status": "Applied",
            "applied_on": date.today().isoformat(),
        }
        labels = {
            "company": "Company *", "role": "Role *", "status": "Status",
            "applied_on": "Applied on (YYYY-MM-DD)",
            "follow_up": "Follow up on (YYYY-MM-DD)", "link": "Job link",
        }
        for i, field in enumerate(labels):
            ttk.Label(self, text=labels[field]).grid(row=i, column=0, sticky="w", padx=8, pady=4)
            var = tk.StringVar(value=initial.get(field) or "")
            if field == "status":
                widget = ttk.Combobox(self, textvariable=var, values=STATUSES, state="readonly")
            else:
                widget = ttk.Entry(self, textvariable=var, width=40)
            widget.grid(row=i, column=1, padx=8, pady=4)
            self.vars[field] = var

        ttk.Label(self, text="Notes").grid(row=len(labels), column=0, sticky="nw", padx=8, pady=4)
        self.notes = tk.Text(self, width=40, height=5)
        self.notes.insert("1.0", initial.get("notes") or "")
        self.notes.grid(row=len(labels), column=1, padx=8, pady=4)

        ttk.Button(self, text="Save", command=self.save).grid(
            row=len(labels) + 1, column=1, sticky="e", padx=8, pady=8
        )
        self.transient(parent)
        self.grab_set()

    def save(self):
        data = {f: v.get().strip() for f, v in self.vars.items()}
        data["notes"] = self.notes.get("1.0", "end").strip()
        try:
            self.on_save(data)
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e), parent=self)
            return
        self.destroy()


class App(tk.Tk):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.title("Job Application Tracker")
        self.geometry("900x500")

        # Toolbar: search, filter, actions
        bar = ttk.Frame(self, padding=6)
        bar.pack(fill="x")
        ttk.Label(bar, text="Search:").pack(side="left")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(bar, textvariable=self.search, width=25).pack(side="left", padx=4)
        ttk.Label(bar, text="Status:").pack(side="left")
        self.status_filter = tk.StringVar(value="All")
        box = ttk.Combobox(bar, textvariable=self.status_filter,
                           values=["All"] + STATUSES, state="readonly", width=12)
        box.pack(side="left", padx=4)
        box.bind("<<ComboboxSelected>>", lambda _: self.refresh())
        for text, cmd in [("Export CSV", self.export), ("Delete", self.delete),
                          ("Edit", self.edit), ("Add", self.add)]:
            ttk.Button(bar, text=text, command=cmd).pack(side="right", padx=2)

        # Table
        self.tree = ttk.Treeview(self, columns=COLUMNS, show="headings")
        for col in COLUMNS:
            self.tree.heading(col, text=col.replace("_", " ").title())
            self.tree.column(col, width=160)
        self.tree.pack(fill="both", expand=True, padx=6)
        self.tree.bind("<Double-1>", lambda _: self.edit())
        self.tree.tag_configure("due", background="#ffe9a8")

        # Status bar with counts
        self.summary = ttk.Label(self, padding=6)
        self.summary.pack(fill="x")

        self.refresh()
        self.after(300, self.remind_follow_ups)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        status = self.status_filter.get()
        due = {r["id"] for r in self.tracker.due_follow_ups()}
        for row in self.tracker.list(None if status == "All" else status, self.search.get()):
            self.tree.insert("", "end", iid=str(row["id"]),
                             values=[row[c] or "" for c in COLUMNS],
                             tags=("due",) if row["id"] in due else ())
        stats = self.tracker.stats()
        self.summary.config(text="   ".join(f"{s}: {n}" for s, n in stats.items())
                            + f"   |   Total: {sum(stats.values())}")

    def selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Nothing selected", "Select an application first.")
            return None
        return int(sel[0])

    def add(self):
        ApplicationForm(self, lambda d: (self.tracker.add(**d), self.refresh()))

    def edit(self):
        app_id = self.selected_id()
        if app_id is not None:
            ApplicationForm(self, lambda d: (self.tracker.update(app_id, **d), self.refresh()),
                            initial=self.tracker.get(app_id))

    def delete(self):
        app_id = self.selected_id()
        if app_id is not None and messagebox.askyesno("Delete", "Delete this application?"):
            self.tracker.delete(app_id)
            self.refresh()

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")])
        if path:
            n = self.tracker.export_csv(path)
            messagebox.showinfo("Exported", f"Saved {n} applications to\n{path}")

    def remind_follow_ups(self):
        due = self.tracker.due_follow_ups()
        if due:
            lines = "\n".join(f"• {r['company']} — {r['role']} (due {r['follow_up']})" for r in due)
            messagebox.showinfo("Follow-ups due", f"Time to follow up on:\n\n{lines}")


def main():
    tracker = Tracker(DB_PATH)
    try:
        App(tracker).mainloop()
    finally:
        tracker.close()


if __name__ == "__main__":
    main()
