import pandas as pd
import io

# Schritt 1: Rohdaten lesen (jede Zeile ist eine lange Textzeile)
roh = pd.read_excel("health_tun.csv", engine="openpyxl", header=None)

# Schritt 2: Alle Zeilen zu einem großen Text zusammenfügen
text = "\n".join(roh[0].astype(str))

# Schritt 3: Diesen Text jetzt richtig als CSV einlesen
df = pd.read_csv(io.StringIO(text))

print(df.head())
print(df.shape)

alle_indikatoren = df["Indicator Name"].unique()
for indikator in alle_indikatoren:
    print(indikator)


suizid = df[df["Indicator Name"] == "Suicide mortality rate (per 100,000 population)"]
print(suizid[["Year", "Value"]].sort_values("Year"))

import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(suizid["Year"], suizid["Value"], marker="o")
plt.title("Suizidrate in Tunesien (2000-2021)")
plt.xlabel("Jahr")
plt.ylabel("Suizidrate (pro 100.000 Einwohner)")
plt.grid(True)
plt.savefig("suizidrate_tunesien.png")
plt.show()


import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import io

roh = pd.read_excel("health_tun.csv", engine="openpyxl", header=None)
text = "\n".join(roh[0].astype(str))
df = pd.read_csv(io.StringIO(text))

suizid = df[df["Indicator Name"] == "Suicide mortality rate (per 100,000 population)"]
suizid = suizid[["Year", "Value"]].sort_values("Year").reset_index(drop=True)

fig, ax = plt.subplots(figsize=(10, 6))

def update(frame):
    ax.clear()
    ax.plot(suizid["Year"][:frame+1], suizid["Value"][:frame+1], marker="o", color="steelblue")
    ax.set_title("Suizidrate in Tunesien (2000-2021)")
    ax.set_xlabel("Jahr")
    ax.set_ylabel("Suizidrate (pro 100.000 Einwohner)")
    ax.set_xlim(suizid["Year"].min(), suizid["Year"].max())
    ax.set_ylim(suizid["Value"].min() - 0.2, suizid["Value"].max() + 0.2)
    ax.grid(True)

ani = animation.FuncAnimation(fig, update, frames=len(suizid), interval=400, repeat=False)
ani.save("suizidrate_animation.gif", writer="pillow")
print("Animation gespeichert!")