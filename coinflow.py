import requests
import time
import threading
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import deque
import numpy as np
from scipy.interpolate import make_interp_spline

# ======== Lista de moedas ========
MOEDAS = [
    "USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD", "CHF", "NZD",
    "MXN", "ARS", "CLP", "INR", "HKD", "ZAR", "SGD", "NOK", "SEK",
    "DKK", "TRY", "KRW"
]

NOMES = {
    "USD": "Dólar Americano",
    "EUR": "Euro",
    "GBP": "Libra Esterlina",
    "JPY": "Iene Japonês",
    "CNY": "Yuan Chinês",
    "CAD": "Dólar Canadense",
    "AUD": "Dólar Australiano",
    "CHF": "Franco Suíço",
    "NZD": "Dólar Neozelandês",
    "MXN": "Peso Mexicano",
    "ARS": "Peso Argentino",
    "CLP": "Peso Chileno",
    "INR": "Rúpia Indiana",
    "HKD": "Dólar de Hong Kong",
    "ZAR": "Rand Sul-Africano",
    "SGD": "Dólar de Cingapura",
    "NOK": "Coroa Norueguesa",
    "SEK": "Coroa Sueca",
    "DKK": "Coroa Dinamarquesa",
    "TRY": "Lira Turca",
    "KRW": "Won Sul-Coreano"
}


# ======== Obter cotações ========
def obter_cotacoes():
    pares = ",".join([f"{m}-BRL" for m in MOEDAS])
    url = f"https://economia.awesomeapi.com.br/json/last/{pares}"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        return {m: float(data[f"{m}BRL"]["bid"]) for m in MOEDAS if f"{m}BRL" in data}
    except Exception as e:
        print("Erro ao obter cotações:", e)
        return {m: None for m in MOEDAS}


# ======== Criação da janela principal ========
def criar_dashboard():
    root = tk.Tk()
    root.title("CoinFlow 🌍💱 - Dashboard de Cotações")
    root.configure(bg="#101010")

    largura, altura = 1000, 700
    x = (root.winfo_screenwidth() - largura) // 2
    y = (root.winfo_screenheight() - altura) // 3
    root.geometry(f"{largura}x{altura}+{x}+{y}")

    titulo = tk.Label(
        root,
        text="🌍 CoinFlow - Cotações Globais (em BRL)",
        font=("Arial", 18, "bold"),
        fg="white",
        bg="#101010"
    )
    titulo.pack(pady=10)

    container = tk.Frame(root, bg="#101010")
    container.pack(expand=True, fill="both", padx=20, pady=10)

    blocos = {}

    # Cria os blocos de moedas
    for moeda in MOEDAS:
        bloco = tk.Frame(container, bg="#1a1a1a", bd=1, relief="solid", padx=5, pady=5)

        lbl_nome = tk.Label(bloco,
                            text=f"{NOMES.get(moeda, moeda)} ({moeda})",
                            font=("Arial", 10, "bold"), fg="white", bg="#1a1a1a")
        lbl_nome.pack(pady=(5, 0))

        lbl_valor = tk.Label(bloco, text="Carregando...",
                             font=("Arial", 14, "bold"),
                             fg="white", bg="#1a1a1a")
        lbl_valor.pack(pady=(0, 2))

        # Mini gráfico detalhado
        fig, ax = plt.subplots(figsize=(3, 1))
        fig.patch.set_alpha(0)
        ax.set_facecolor("#1a1a1a")
        plt.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.15)
        linha, = ax.plot([], [], color="white", linewidth=1.2)
        ax.tick_params(colors="#777", labelsize=6)
        ax.grid(True, color="#333", linestyle="--", linewidth=0.5, alpha=0.5)
        for spine in ax.spines.values():
            spine.set_color("#333")

        canvas_plot = FigureCanvasTkAgg(fig, master=bloco)
        canvas_plot.get_tk_widget().pack(fill="x", expand=False, padx=5, pady=(0, 5))

        blocos[moeda] = {
            "frame": bloco,
            "lbl_valor": lbl_valor,
            "linha": linha,
            "ax": ax,
            "canvas": canvas_plot,
            "historico": deque(maxlen=40),
            "ultimo": None,
            "preenchimento": None
        }

    # Reorganiza blocos automaticamente conforme largura da janela
    def reposicionar_blocos(event=None):
        largura_total = container.winfo_width()
        blocos_por_linha = max(1, largura_total // 250)  # largura mínima por bloco
        for widget in container.winfo_children():
            widget.grid_forget()
        for i, moeda in enumerate(MOEDAS):
            bloco = blocos[moeda]["frame"]
            bloco.grid(row=i // blocos_por_linha, column=i % blocos_por_linha,
                       padx=8, pady=8, sticky="nsew")
        for c in range(blocos_por_linha):
            container.columnconfigure(c, weight=1)

    container.bind("<Configure>", reposicionar_blocos)

    return root, blocos


# ======== Atualização das moedas ========
def atualizar(blocos):
    while True:
        cotacoes = obter_cotacoes()
        for moeda, valor in cotacoes.items():
            bloco = blocos.get(moeda)
            if not bloco or valor is None:
                continue

            anterior = bloco["ultimo"]
            cor = "white"
            if anterior is not None:
                if valor < anterior:
                    cor = "#00FF66"
                elif valor > anterior:
                    cor = "#FF5555"

            bloco["lbl_valor"].config(text=f"R$ {valor:.4f}", fg=cor)
            bloco["historico"].append(valor)

            x = np.arange(len(bloco["historico"]))
            y = np.array(bloco["historico"])

            if len(y) > 3:
                x_suave = np.linspace(x.min(), x.max(), 150)
                spline = make_interp_spline(x, y, k=3)
                y_suave = spline(x_suave)
            else:
                x_suave, y_suave = x, y

            bloco["linha"].set_data(x_suave, y_suave)
            bloco["ax"].relim()
            bloco["ax"].autoscale_view()
            bloco["linha"].set_color(cor)

            if bloco["preenchimento"]:
                bloco["preenchimento"].remove()
            bloco["preenchimento"] = bloco["ax"].fill_between(
                x_suave, y_suave, color=cor, alpha=0.15
            )

            bloco["canvas"].draw_idle()
            bloco["ultimo"] = valor
        time.sleep(5)


# ======== Execução principal ========
if __name__ == "__main__":
    dashboard, blocos = criar_dashboard()
    t = threading.Thread(target=atualizar, args=(blocos,), daemon=True)
    t.start()
    dashboard.mainloop()
