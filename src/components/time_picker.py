"""
Componente reutilizable de selección de hora (Spinbox Dual HH:MM).

Provee un control visual con dos Spinboxes numéricos para hora y minutos,
formateo con ceros a la izquierda y métodos get_time() / set_time().
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional


class TimePickerDual(ttk.Frame):
    """
    Control de entrada de hora dual: [ HH ▲▼ ] : [ MM ▲▼ ]
    """

    def __init__(
        self,
        parent: tk.Widget,
        hora_inicial: int = 8,
        minuto_inicial: int = 0,
        step_minutos: int = 15,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)

        self.hora_var = tk.StringVar(value=f"{hora_inicial:02d}")
        self.min_var = tk.StringVar(value=f"{minuto_inicial:02d}")

        self._crear_widgets(step_minutos)

    def _crear_widgets(self, step_minutos: int) -> None:
        # Spinbox para Horas (00 a 23)
        self.spin_hora = ttk.Spinbox(
            self,
            from_=0,
            to=23,
            wrap=True,
            width=3,
            justify="center",
            textvariable=self.hora_var,
            font=("Segoe UI", 10),
            command=self._formatear_hora,
        )
        self.spin_hora.pack(side="left")
        self.spin_hora.bind("<FocusOut>", lambda e: self._formatear_hora())

        # Separador ':'
        sep_lbl = ttk.Label(self, text=":", font=("Segoe UI", 11, "bold"))
        sep_lbl.pack(side="left", padx=3)

        # Minutos en intervalos configurables (por defecto 00, 15, 30, 45)
        if step_minutos in (15, 30):
            valores_minutos = [f"{m:02d}" for m in range(0, 60, step_minutos)]
            self.spin_min = ttk.Spinbox(
                self,
                values=valores_minutos,
                wrap=True,
                width=3,
                justify="center",
                textvariable=self.min_var,
                font=("Segoe UI", 10),
                command=self._formatear_minutos,
            )
        else:
            self.spin_min = ttk.Spinbox(
                self,
                from_=0,
                to=59,
                wrap=True,
                width=3,
                justify="center",
                textvariable=self.min_var,
                font=("Segoe UI", 10),
                command=self._formatear_minutos,
            )

        self.spin_min.pack(side="left")
        self.spin_min.bind("<FocusOut>", lambda e: self._formatear_minutos())

    def _formatear_hora(self) -> None:
        try:
            val = int(self.hora_var.get())
            val = max(0, min(23, val))
            self.hora_var.set(f"{val:02d}")
        except (ValueError, TypeError):
            self.hora_var.set("08")

    def _formatear_minutos(self) -> None:
        try:
            val = int(self.min_var.get())
            val = max(0, min(59, val))
            self.min_var.set(f"{val:02d}")
        except (ValueError, TypeError):
            self.min_var.set("00")

    def get_time(self) -> str:
        """Retorna la hora seleccionada en formato HH:MM (ej. '08:30')."""
        self._formatear_hora()
        self._formatear_minutos()
        return f"{self.hora_var.get()}:{self.min_var.get()}"

    def set_time(self, time_str: str) -> None:
        """
        Configura la hora a partir de un string 'HH:MM'.
        Si el formato es inválido, ignora el cambio.
        """
        try:
            partes = time_str.strip().split(":")
            if len(partes) >= 2:
                hora = int(partes[0])
                minuto = int(partes[1][:2])
                if 0 <= hora <= 23 and 0 <= minuto <= 59:
                    self.hora_var.set(f"{hora:02d}")
                    self.min_var.set(f"{minuto:02d}")
        except Exception:
            pass
