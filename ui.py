import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from db import insert_transaction, fetch_all, init_db
from utils import today_iso
import csv

def add_transaction():
    t_type = type_var.get()
    category = category_entry.get().strip()
    amount_text = amount_entry.get().strip()
    note = note_entry.get().strip()
    date_text = date_entry.get().strip() or today_iso()

    if not category or not amount_text:
        messagebox.showwarning("Validation", "Category and amount required.")
        return
    try:
        amount = float(amount_text)
    except ValueError:
        messagebox.showwarning("Validation", "Amount must be numeric.")
        return

    insert_transaction(t_type, category, amount, date_text, note)
    messagebox.showinfo("Success", "Transaction added.")
    refresh_table()

def refresh_table():
    for i in tree.get_children():
        tree.delete(i)
    for row in fetch_all():
        tree.insert("", tk.END, values=(row["id"], row["t_type"], row["category"], row["amount"], row["date"], row["note"]))

def export_csv():
    rows = fetch_all()
    if not rows:
        messagebox.showinfo("Export", "No data to export.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files","*.csv")])
    if not path:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID","Type","Category","Amount","Date","Note"])
        for r in rows:
            writer.writerow([r["id"], r["t_type"], r["category"], r["amount"], r["date"], r["note"]])
    messagebox.showinfo("Export", f"Exported to {path}")

def main():
    init_db()
    global type_var, category_entry, amount_entry, note_entry, date_entry, tree
    root = tk.Tk()
    root.title("Personal Finance Tracker")

    frame = ttk.Frame(root, padding=10)
    frame.grid()

    ttk.Label(frame, text="Type").grid(row=0, column=0)
    type_var = tk.StringVar(value="Expense")
    ttk.OptionMenu(frame, type_var, "Expense", "Expense", "Income").grid(row=0, column=1)

    ttk.Label(frame, text="Category").grid(row=1, column=0)
    category_entry = ttk.Entry(frame); category_entry.grid(row=1, column=1)

    ttk.Label(frame, text="Amount").grid(row=2, column=0)
    amount_entry = ttk.Entry(frame); amount_entry.grid(row=2, column=1)

    ttk.Label(frame, text="Date").grid(row=3, column=0)
    date_entry = ttk.Entry(frame); date_entry.insert(0, today_iso()); date_entry.grid(row=3, column=1)

    ttk.Label(frame, text="Note").grid(row=4, column=0)
    note_entry = ttk.Entry(frame); note_entry.grid(row=4, column=1)

    ttk.Button(frame, text="Add Transaction", command=add_transaction).grid(row=5, column=0, columnspan=2, pady=5)
    ttk.Button(frame, text="Export CSV", command=export_csv).grid(row=6, column=0, columnspan=2)

    cols = ("ID", "Type", "Category", "Amount", "Date", "Note")
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
    tree.grid(row=7, column=0, columnspan=2, pady=10)
    refresh_table()

    root.mainloop()

if __name__ == "__main__":
    main()
