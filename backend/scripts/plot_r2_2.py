import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# 字体改为 Arial
plt.rcParams.update({
    'font.family':        'sans-serif',
    'font.sans-serif':    ['Arial', 'DejaVu Sans'],
    'font.size':          9,
    'axes.linewidth':     0.5,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'axes.spines.left':   False,
    'xtick.labelsize':    9,
    'ytick.labelsize':    9,
    'xtick.major.width':  0.5,
    'ytick.major.width':  0,
    'xtick.direction':    'out',
    'grid.linewidth':     0.3,
    'grid.alpha':         0.4,
})

# ── data (sorted by Cover ascending) ─────────────────────────────────────────
rows = [
    ('overflow handling',       'Visual/layout',          17.4,  37.6,  45.0),
    ('animation consistency',   'Visual/layout',          18.8,  56.3,  24.9),
    ('monotonicity',            'Input/prop',             24.5,  53.5,  22.0),
    ('visual alignment',        'Visual/layout',          27.9,  40.8,  31.4),
    ('context propagation',     'Composition/context',    30.2,  41.5,  28.3),
    ('responsive sizing',       'Visual/layout',          34.8,  43.4,  21.8),
    ('keyboard interaction',    'Interaction/accessib.',  36.1,  39.1,  24.7),
    ('focus management',        'Interaction/accessib.',  40.1,  40.0,  20.0),
]

labels    = [r[0] for r in rows]
top_level = [r[1] for r in rows]
cover     = np.array([r[2] for r in rows])
weak      = np.array([r[3] for r in rows])
untouched = np.array([r[4] for r in rows])

# ── optimised colour palette ──────────────────────────────────────────────────
cat_colors = {
    'Visual/layout':         '#4d8cbf',
    'Input/prop':            '#e8823b',
    'Composition/context':   '#5b8c5a',
    'Interaction/accessib.': '#c49a4a',
}
COVER_C     = '#3266ad'
WEAK_C      = '#7da4ce'
UNTOUCHED_C = '#e89878'

# ── figure (adjust top to leave room for legend) ─────────────────────────────
fig, ax = plt.subplots(figsize=(7, 3.5))
fig.subplots_adjust(left=0.22, right=0.72, top=0.88, bottom=0.15)

y = np.arange(len(labels))
H = 0.52

# ── stacked bars ──────────────────────────────────────────────────────────────
ax.barh(y, cover,     height=H, color=COVER_C,     label='Cover',       zorder=3)
ax.barh(y, weak,      height=H, color=WEAK_C,      label='Weak-oracle', zorder=3, left=cover)
ax.barh(y, untouched, height=H, color=UNTOUCHED_C, label='Untouched',   zorder=3, left=cover+weak)

# ── value labels ──────────────────────────────────────────────────────────────
for i in range(len(labels)):
    if cover[i] >= 8:
        ax.text(cover[i] / 2, y[i], f'{cover[i]:.1f}',
                ha='center', va='center', fontsize=8, color='white', weight='bold')
    if weak[i] >= 12:
        ax.text(cover[i] + weak[i] / 2, y[i], f'{weak[i]:.1f}',
                ha='center', va='center', fontsize=8, color='white', weight='bold')
    if untouched[i] >= 12:
        ax.text(cover[i] + weak[i] + untouched[i] / 2, y[i], f'{untouched[i]:.1f}',
                ha='center', va='center', fontsize=8, color='white', weight='bold')

# ── y-axis ────────────────────────────────────────────────────────────────────
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=10, )
ax.tick_params(axis='y', length=0, pad=4)

# ── x-axis ────────────────────────────────────────────────────────────────────
ax.set_xlim(0, 100)
ax.set_ylim(-0.5, len(labels) - 0.5)
ax.set_xlabel('Proportion of MRs (%)', fontsize=9, labelpad=4)
ax.xaxis.grid(True, linestyle=':', zorder=0)
ax.set_axisbelow(True)
ax.set_xticks([0, 25, 50, 75, 100])
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v)}%'))

# ── category brackets on right side ──────────────────────────────────────────
seen = {}
seen_order = []
for i, tl in enumerate(top_level):
    if tl not in seen:
        seen[tl] = []
        seen_order.append(tl)
    seen[tl].append(i)

X_BRACK = 102
X_TEXT  = 108

for tl in seen_order:
    idxs  = seen[tl]
    col   = cat_colors[tl]
    top_y = max(idxs) + H / 2
    bot_y = min(idxs) - H / 2
    mid_y = (top_y + bot_y) / 2
    ax.plot([X_BRACK, X_BRACK], [bot_y, top_y],
            color=col, lw=3.0, clip_on=False,
            solid_capstyle='round', transform=ax.transData)
    ax.plot([X_BRACK, X_BRACK - 1], [bot_y, bot_y],
            color=col, lw=2, clip_on=False, transform=ax.transData)
    ax.plot([X_BRACK, X_BRACK - 1], [top_y, top_y],
            color=col, lw=2, clip_on=False, transform=ax.transData)
    # ax.text(X_TEXT, mid_y, tl,
    #         ha='left', va='center', fontsize=7,
    #         color=col, fontstyle='normal',
    #         clip_on=False, transform=ax.transData)

# ── legend: placed above the figure, one row (ncol=3) ─────────────────────────
seg_patches = [
    mpatches.Patch(color=COVER_C,     label='Cover'),
    mpatches.Patch(color=WEAK_C,      label='Weak-oracle'),
    mpatches.Patch(color=UNTOUCHED_C, label='Untouched'),
]
ax.legend(handles=seg_patches,
          loc='upper center', bbox_to_anchor=(0.5, 1.10),
          ncol=3, frameon=False, fontsize=9,
          handlelength=1.0, columnspacing=1.0)

# ── no title (removed) ────────────────────────────────────────────────────────
# ax.set_title(...) 已注释

# ── export ────────────────────────────────────────────────────────────────────
for ext in ('pdf', 'png'):
    fig.savefig(f'fig_worst_cover_arial_nolegend_overlap.{ext}',
                dpi=600, bbox_inches='tight',
                format=ext, transparent=(ext == 'pdf'))
    print(f'Saved fig_worst_cover_arial_nolegend_overlap.{ext}')

plt.close(fig)