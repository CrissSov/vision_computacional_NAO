# angle_interface.py
import tkinter as tk
from tkinter import ttk

class AngleInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("Ángulos NAO")

        self.sent_table = ttk.Treeview(root, columns=("Joint", "Angle"), show='headings', height=10)
        self.sent_table.heading("Joint", text="Articulación")
        self.sent_table.heading("Angle", text="Ángulo Enviado (°)")
        self.sent_table.grid(row=0, column=0, padx=10, pady=10)

        self.recv_table = ttk.Treeview(root, columns=("Joint", "Angle"), show='headings', height=10)
        self.recv_table.heading("Joint", text="Articulación")
        self.recv_table.heading("Angle", text="Ángulo Recibido (°)")
        self.recv_table.grid(row=0, column=1, padx=10, pady=10)

    def update_sent_angles(self, angles_dict):
        self.sent_table.delete(*self.sent_table.get_children())
        for joint, angle in angles_dict.items():
            self.sent_table.insert("", "end", values=(joint, f"{angle:.2f}"))

    def update_recv_angles(self, angles_dict):
        self.recv_table.delete(*self.recv_table.get_children())
        for joint, angle in angles_dict.items():
            self.recv_table.insert("", "end", values=(joint, f"{angle:.2f}"))
