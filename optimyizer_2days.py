from pyomo.environ import *

# Zeitauflösung: 15 Minuten
TIMEPOINTS = range(96)  # 24*4 = 96 Zeitpunkte pro Tag
DAYS = [0, 1]  # Aktueller Tag und nächster Tag

# Beispiel PV Ertrag und Prognose für den nächsten Tag
PV_prod = {
    (0, t): (
        0 if t < 16 or t > 80 else 
        (0.1 * 4.8 if t < 32 else 
         0.7 * 4.8 if t < 48 else 
         0.9 * 4.8 if t < 64 else 
         0.4 * 4.8)
    ) for t in TIMEPOINTS
}

# Fügen Sie die Ertragsprognose für den nächsten Tag (Tag 1) analog hinzu
PV_prod.update({
    (1, t): (
        0 if t < 16 or t > 80 else 
        (0.2 * 4.8 if t < 32 else 
         0.8 * 4.8 if t < 48 else 
         0.6 * 4.8 if t < 64 else 
         0.3 * 4.8)
    ) for t in TIMEPOINTS
})

# Modell
model = ConcreteModel()

# Variablen
BatteryCapacity = 10  # Beispielswert: Kapazität des Batteriespeichers in kWh
model.E_battery = Var(DAYS, TIMEPOINTS, within=NonNegativeReals, bounds=(0, BatteryCapacity))  
model.E_grid = Var(DAYS, TIMEPOINTS, within=NonNegativeReals)  
model.E_feedin = Var(DAYS, TIMEPOINTS, within=NonNegativeReals)  

# Beispielwerte für Load und FeedInTarif (ersetzen Sie diese durch Ihre eigenen Daten)
Load = {t: 1.0 for t in TIMEPOINTS}
FeedInTarif = {t: 0.12 for t in TIMEPOINTS}

# Zielfunktion
def objective_rule(model):
    return -sum(FeedInTarif[t] * model.E_feedin[d, t] for d in DAYS for t in TIMEPOINTS) + sum(model.E_grid[d, t] for d in DAYS for t in TIMEPOINTS)

model.objective = Objective(rule=objective_rule, sense=minimize)

# Energiebilanz
def energy_balance_rule(model, d, t):
    prev_storage = model.E_battery[d, t-1] if t > 0 else model.E_battery[d-1, TIMEPOINTS[-1]] if d > 0 else 0
    return (PV_prod[d, t] + model.E_grid[d, t] - model.E_feedin[d, t] + prev_storage == Load[t] + model.E_battery[d, t])

model.energy_balance = Constraint(DAYS, TIMEPOINTS, rule=energy_balance_rule)

# Jetzt das Modell mit einem Solver lösen
solver = SolverFactory('glpk')
solver.solve(model)

# Ergebnisse ausgeben
for d in DAYS:
    print(f"Tag {d+1}:")
    for t in TIMEPOINTS:
        hour, minute = divmod(t*15, 60)
        print(f"  Uhrzeit {hour:02d}:{minute:02d}: PV Ertrag {PV_prod[d, t]:.2f} kWh, Batterie {model.E_battery[d, t]():.2f} kWh, Netzbezug {model.E_grid[d, t]():.2f} kWh, Netzeinspeisung {model.E_feedin[d, t]():.2f} kWh")
