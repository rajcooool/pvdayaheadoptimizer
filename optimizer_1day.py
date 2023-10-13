from pyomo.environ import *

# Zeitauflösung: 15 Minuten
TIMEPOINTS = range(96)  # 24*4 = 96 Zeitpunkte pro Tag

# Typischer Ertrag einer 4,8 kW PV-Anlage im Sommer (vereinfacht)
PV_prod = {
    t: 0 if t < 16 or t > 80 else
    0.1 * 4.8 if t < 32 else
    0.7 * 4.8 if t < 48 else
    0.9 * 4.8 if t < 64 else
    0.4 * 4.8
    for t in TIMEPOINTS
}

Load = {t: 1 for t in TIMEPOINTS}  # Beispiel: konstanter Verbrauch von 1 kWh pro 15 Minuten

# Beispiel Feed-in-Tarif (in €/kWh)
FeedInTarif = {
    t: 0.06 if t < 32 else  
    0.03 if t < 64 else     
    0.07 if t < 80 else     
    0.10                    
    for t in TIMEPOINTS
}

BatteryCapacity = 10  # 10 kWh Speicherkapazität

# Modell
model = ConcreteModel()

# Variablen
model.E_battery = Var(TIMEPOINTS, within=NonNegativeReals, bounds=(0, BatteryCapacity))  # Energie im Speicher
model.E_grid = Var(TIMEPOINTS, within=NonNegativeReals)  # Energie aus dem Netz
model.E_feedin = Var(TIMEPOINTS, within=NonNegativeReals)  # Energie in das Netz eingespeist

# Zielfunktion: Minimiere Netzbezug, Maximiere Erträge aus Netzeinspeisung
def objective_rule(model):
    return - sum(FeedInTarif[t] * model.E_feedin[t] for t in TIMEPOINTS) + sum(model.E_grid[t] for t in TIMEPOINTS)

model.objective = Objective(rule=objective_rule, sense=minimize)

# Energiebilanz für jeden Zeitpunkt
def energy_balance_rule(model, t):
    prev_storage = model.E_battery[t-1] if t > 0 else 0
    return (PV_prod[t] + model.E_grid[t] - model.E_feedin[t] + prev_storage == 
            Load[t] + model.E_battery[t])

model.energy_balance = Constraint(TIMEPOINTS, rule=energy_balance_rule)

# Jetzt das Modell mit einem Solver lösen
solver = SolverFactory('glpk')
solver.solve(model)

# Ergebnisse ausgeben
for t in TIMEPOINTS:
    hour, minute = divmod(t*15, 60)
    print(f"Uhrzeit {hour:02d}:{minute:02d}: PV Ertrag {PV_prod[t]:.2f} kWh, Batterie {model.E_battery[t]():.2f} kWh, Netzbezug {model.E_grid[t]():.2f} kWh, Netzeinspeisung {model.E_feedin[t]():.2f} kWh")
