#!/uscer/bin/env python3

from os.path import basename, splitext, exists
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import datetime
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
    name = "Foo"
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
            text="Automacitky stahovat kurzovní lístek",
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
        )
        self.rbtnSale = tk.Radiobutton(
            self.lblTransaction,
            text="Prodej",
            variable=self.varTransaction,
            value="sale",
        )
        self.varTransaction.trace_add("write", self.transactionClick)
        self.rbtnPurchase.pack()
        self.rbtnSale.pack()

        self.cboxCountry = ttk.Combobox(self, values=[])
        self.cboxCountry.set("Vyber zemi...")
        self.cboxCountry.pack(anchor="w", padx=5, pady=5)
        self.cboxCountry.bind("<<ComboboxSelected>>", self.on_select)

        self.lblCourse = tk.LabelFrame(self, text="Kurz")
        self.lblCourse.pack(anchor="w", padx=5, pady=5)
        self.entryAmount = MyEntry(self.lblCourse, state="readonly")
        self.entryAmount.pack()
        self.entryRate = MyEntry(self.lblCourse, state="readonly")
        self.entryRate.pack()

        self.btn = tk.Button(self, text="Quit", command=self.quit)
        self.btn.pack()

        self.read_ticket()
        self.on_select()

    def transactionClick(self, *arg):
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
        # stahuju aktuální kurzovní lístek z https://www.cnb.cz/en/financial_markets/foreign_exchange_market/exchange_rate_fixing/daily.txt
        # a uložím jej do souboru currency_exchange_rate.txt
        URL = "https://www.cnb.cz/en/financial_markets/foreign_exchange_market/exchange_rate_fixing/daily.txt"
        try:
            response = requests.get(URL)
            data = response.text
            with open(self.filename, "w") as f:
                f.write(data)
        except requests.exceptions.ConnectionError as e:
            print(f"Error: {e}")
        self.read_ticket()
        self.on_select()

    def read_ticket(self):
        if not exists(self.filename):
            messagebox.showerror("Chyba:", "Kurzovní lístek nennalezen!")
            return
        with open(self.filename, "r") as f:
            data = f.read()
        self.ticket = {}
        for line in data.splitlines()[2:]:
            country, currency, amount, code, rate = line.split("|")
            self.ticket[country] = {
                "currency": currency,
                "amount": amount,
                "code": code,
                "rate": rate,
            }
        self.cboxCountry.config(values=list(self.ticket.keys()))

    def autoDownload(self):
        self.download()
        messagebox.showinfo("Download", "Bylo provedeno automatické stažení")
        if self.varAuto.get():
            self.autoID = self.after(20e3, self.autoDownload)

    def on_select(self, event=None):
        country = self.cboxCountry.get()
        if country == "Vyber zemi...":
            country = list(self.ticket.keys())[0]
            self.cboxCountry.set(country)
        self.lblCourse.config(text=self.ticket[country]["code"])
        self.amount = int(self.ticket[country]["amount"])
        if self.varTransaction.get() == "purchase":
            self.rate = float(self.ticket[country]["rate"]) * 0.96
        else:
            self.rate = float(self.ticket[country]["rate"]) * 1.04
        self.entryAmount.value = str(self.amount)
        self.entryRate.value = str(self.rate)

    def quit(self, event=None):
        super().destroy()


app = Application()
app.mainloop()
