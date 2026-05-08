import fastf1
import matplotlib.pyplot as plt

fastf1.Cache.enable_cache('data/cache')

print("Loading Bahrain 2023 session...")
session = fastf1.get_session(2023, 'Bahrain', 'R')
session.load(telemetry=True, weather=False, messages=False)

print("Getting fastest lap telemetry...")
lap = session.laps.pick_fastest()
pos = lap.get_pos_data()

x = pos['X'].values
y = pos['Y'].values

fig, ax = plt.subplots(figsize=(10, 8), facecolor='#080b12')
ax.set_facecolor('#080b12')

ax.plot(x, y, color='#1e2535', linewidth=12, solid_capstyle='round', solid_joinstyle='round', zorder=1)
ax.plot(x, y, color='#00d4ff', linewidth=3, solid_capstyle='round', solid_joinstyle='round', zorder=2)
ax.plot(x, y, color='#ffffff', linewidth=0.8, solid_capstyle='round', solid_joinstyle='round', zorder=3, alpha=0.4)

start_x, start_y = x[0], y[0]
ax.scatter([start_x], [start_y], color='#e10600', s=120, zorder=5)
ax.scatter([start_x], [start_y], color='#ff4444', s=40, zorder=6)

ax.text(start_x + 100, start_y - 150,
    'START/FINISH',
    color='#e10600',
    fontsize=7,
    fontfamily='monospace',
    zorder=7
)

ax.text(0.02, 0.98,
    'BAHRAIN INTERNATIONAL CIRCUIT',
    transform=ax.transAxes,
    color='#00d4ff',
    fontsize=9,
    fontfamily='monospace',
    verticalalignment='top',
    alpha=0.7
)

ax.text(0.02, 0.93,
    '2023 · Round 1 · 5.412 km',
    transform=ax.transAxes,
    color='#445566',
    fontsize=7,
    fontfamily='monospace',
    verticalalignment='top'
)

ax.axis('off')
ax.set_aspect('equal')

plt.tight_layout(pad=0)
plt.savefig('../frontend/public/bahrain_circuit.png',
    dpi=150,
    bbox_inches='tight',
    facecolor='#080b12',
    transparent=False
)

print("✅ Circuit saved to frontend/public/bahrain_circuit.png")