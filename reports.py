import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

def show_report():
    conn = sqlite3.connect("finance.db")
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    if df.empty:
        print("No data to display.")
        return
    summary = df.groupby("t_type")["amount"].sum()
    print(summary)
    summary.plot(kind="bar", title="Income vs Expense")
    plt.show()

if __name__ == "__main__":
    show_report()
