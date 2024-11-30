#!/usr/bin/env python3

from os.path import exists
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import requests


class MyEntry(tk.Entry):
    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master, cnf, **kw)

        if "textvariable" not in kw:
            self.variable = tk.StringVar()
            self.config(textvariable=self.variable)
        else:
            self.variable = kw["textvariable"]

    @property
    def value(self):
        return self.variable.get()

    @value.setter
    def value(self, new: str):
        self.variable.set(new)


class Application(tk.Tk):
    name = "Směnárna"
    filename = "kurzovni_listek.txt"

    def __init__(self):
        super().__init__(className=self.name)
        self.title(self.name)
        self.bind("<Escape>", self.quit)

        self.lbl = tk.Label(self, text="Směnárna")
        self.lbl.pack()

        self.varAuto = tk.BooleanVar()
        self.chbtnAuto = tk.Checkbutton(
            self,
            text="Automaticky stahovat kurzovní lístek",
            variable=self.varAuto,
            command=self.chbtnAutoClick,
        )
        self.chbtnAuto.pack()

        self.btnDownload = tk.Button(
            self, text="Stáhnout kurzovní lístek", command=self.download
        )
        self.btnDownload.pack()

        self.lblTransaction = tk.LabelFrame(self, text="Transakce")
        self.lblTransaction.pack(anchor="w", padx=5)
        self.varTransaction = tk.StringVar(value="purchase")

        self.rbtnPurchase = tk.Radiobutton(
            self.lblTransaction,
            text="Nákup",
            variable=self.varTransaction,
            value="purchase",
            command=self.on_select,
        )
        self.rbtnSale = tk.Radiobutton(
            self.lblTransaction,
            text="Prodej",
            variable=self.varTransaction,
            value="sale",
            command=self.on_select,
        )
        self.rbtnPurchase.pack()
        self.rbtnSale.pack()

        self.cboxCountry = ttk.Combobox(self, values=[])
        self.cboxCountry.set("Vyber zemi...")
        self.cboxCountry.pack(anchor="w", padx=5, pady=5)
        self.cboxCountry.bind("<<ComboboxSelected>>", self.on_select)

        self.lblCourse = tk.LabelFrame(self, text="Kurz")
        self.lblCourse.pack(anchor="w", padx=5, pady=5)

        self.entryAmount = MyEntry(self.lblCourse)
        self.entryAmount.pack()
        self.entryAmount.variable.trace_add("write", self.calculate_conversion)

        self.entryRate = MyEntry(self.lblCourse, state="readonly")
        self.entryRate.pack()

        self.btnQuit = tk.Button(self, text="Quit", command=self.quit)
        self.btnQuit.pack()

        self.ticket = {}
        self.read_ticket()
        self.on_select()

    def chbtnAutoClick(self):
        if self.varAuto.get():
            self.btnDownload.config(state="disabled")
            self.download()
            self.autoID = self.after(20000, self.autoDownload)
        else:
            self.btnDownload.config(state=tk.NORMAL)
            self.after_cancel(self.autoID)

    def download(self):
        URL = "https://www.cnb.cz/en/financial_markets/foreign_exchange_market/exchange_rate_fixing/daily.txt"
        try:
            response = requests.get(URL)
            response.raise_for_status()
            data = response.text
            with open(self.filename, "w") as f:
                f.write(data)
            self.read_ticket()
            self.on_select()
        except requests.RequestException as e:
            messagebox.showerror("Chyba při stahování", f"Nelze stáhnout kurzovní lístek: {e}")

    def read_ticket(self):
        if not exists(self.filename):
            messagebox.showerror("Chyba", "Kurzovní lístek nenalezen!")
            return
        with open(self.filename, "r") as f:
            data = f.read()
        self.ticket.clear()
        for line in data.splitlines()[2:]:
            try:
                country, currency, amount, code, rate = line.split("|")
                self.ticket[country] = {
                    "currency": currency,
                    "amount": int(amount),
                    "code": code,
                    "rate": float(rate),
                }
            except ValueError:
                continue
        self.cboxCountry.config(values=list(self.ticket.keys()))

    def autoDownload(self):
        self.download()
        messagebox.showinfo("Download", "Bylo provedeno automatické stažení")
        if self.varAuto.get():
            self.autoID = self.after(20000, self.autoDownload)

    def on_select(self, event=None):
        country = self.cboxCountry.get()
        if country not in self.ticket:
            if self.ticket:
                country = list(self.ticket.keys())[0]
                self.cboxCountry.set(country)
            else:
                self.entryAmount.value = ""
                self.entryRate.value = ""
                return

        self.lblCourse.config(text=self.ticket[country]["code"])
        self.amount = self.ticket[country]["amount"]

        if self.varTransaction.get() == "purchase":
            self.rate = self.ticket[country]["rate"] * 0.96
        else:
            self.rate = self.ticket[country]["rate"] * 1.04

        self.calculate_conversion()

    def calculate_conversion(self, *args):
        try:
            entered_amount = float(self.entryAmount.value)
            converted_value = entered_amount * self.rate / self.amount
            self.entryRate.value = f"{converted_value:.2f}"
        except ValueError:
            self.entryRate.value = ""

    def quit(self, event=None):
        self.destroy()


if __name__ == "__main__":
    app = Application()
    app.mainloop()
