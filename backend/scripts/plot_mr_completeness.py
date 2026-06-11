import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── colour palette ────────────────────────────────────────────────────────────
BLUE_HI  = '#3266ad'
BLUE_MID = '#7da4ce'
BLUE_LO  = '#b8d0e8'
RED_HI   = '#d85a30'
RED_MID  = '#e89878'
RED_LO   = '#f2c8b8'

# ── typography (Arial) ────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family':        'sans-serif',
    'font.sans-serif':    ['Arial', 'DejaVu Sans'],
    'font.size':          8,
    'axes.titlesize':     6.5,
    'axes.labelsize':     6.5,
    'xtick.labelsize':    6,
    'ytick.labelsize':    5.5,
    'legend.fontsize':    6,
    'axes.linewidth':     0.5,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'xtick.major.width':  0.5,
    'ytick.major.width':  0.5,
    'xtick.direction':    'out',
    'ytick.direction':    'out',
    'grid.linewidth':     0.35,
    'grid.alpha':         0.35,
})

# ── data ──────────────────────────────────────────────────────────────────────
lib_labels = ['ant-design', 'element-plus', 'base-ui', 'material-ui']
lib_data = {
    'T_gem':  [88.2, 85.4, 89.4, 88.6],
    'T_deep': [83.0, 78.3, 84.4, 78.0],
    'T_gpt':  [82.7, 81.2, 86.8, 83.1],
    'C_gem':  [45.0, 54.7, 45.7, 41.9],
    'C_deep': [40.9, 50.3, 43.7, 41.5],
    'C_gpt':  [38.1, 50.5, 40.8, 37.6],
}

cat_labels = ['Data display', 'Feedback', 'Inputs', 'Layout', 'Navigation']
cat_data = {
    'T_gem':  [84.8, 88.1, 89.3, 76.0, 93.7],
    'T_deep': [74.5, 80.4, 87.9, 60.2, 86.8],
    'T_gpt':  [79.4, 80.6, 88.9, 67.2, 87.3],
    'C_gem':  [40.1, 45.6, 57.8, 37.6, 47.1],
    'C_deep': [36.5, 44.9, 56.3, 22.7, 46.0],
    'C_gpt':  [36.1, 36.4, 55.9, 25.2, 41.5],
}

# ── layout ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(8, 2.6))
fig.subplots_adjust(wspace=0.4, left=0.07, right=0.96, top=0.92, bottom=0.30)

BAR_W   = 0.12
OFFSETS = np.array([-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]) * BAR_W
COLORS  = [BLUE_HI, BLUE_MID, BLUE_LO, RED_HI, RED_MID, RED_LO]
KEYS    = ['T_gem', 'T_deep', 'T_gpt', 'C_gem', 'C_deep', 'C_gpt']

def draw_panel(ax, x_labels, data, subtitle):
    n = len(x_labels)
    x = np.arange(n)
    bars = {}
    for i, (key, col) in enumerate(zip(KEYS, COLORS)):
        bar = ax.bar(x + OFFSETS[i], data[key],
                     width=BAR_W * 0.92,
                     color=col,
                     linewidth=0.0,
                     zorder=3)
        bars[key] = bar

    # 为每个 bar 添加数值标签（旋转90度）
    for j in range(n):
        for key in KEYS:
            val = data[key][j]
            rect = bars[key][j]
            # 垂直偏移：条形顶部上方 1.5 个百分点
            ax.text(rect.get_x() + rect.get_width()/2., rect.get_height() + 6,
                    f'{val:.1f}', ha='center', va='center',
                    fontsize=5, color='black', weight='normal', rotation=90)

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=6.5)
    ax.set_ylim(0, 104)   # 为标签留出空间
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v)}%'))
    ax.yaxis.grid(True, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title(subtitle, fontsize=7, fontweight='bold', pad=6, loc='left')

draw_panel(axes[0], lib_labels, lib_data, '(a) By library')
draw_panel(axes[1], cat_labels, cat_data, '(b) By component category')

# ── legend (vertically stacked in the middle gap) ─────────────────────────────
touch_handles = [
    mpatches.Patch(facecolor=BLUE_HI,  label='Gemini'),
    mpatches.Patch(facecolor=BLUE_MID, label='DeepSeek'),
    mpatches.Patch(facecolor=BLUE_LO,  label='GPT'),
]
cover_handles = [
    mpatches.Patch(facecolor=RED_HI,   label='Gemini'),
    mpatches.Patch(facecolor=RED_MID,  label='DeepSeek'),
    mpatches.Patch(facecolor=RED_LO,   label='GPT'),
]

leg_touch = fig.legend(handles=touch_handles, loc='center',
                       bbox_to_anchor=(0.5, 0.8), ncol=1, frameon=False,
                       title='Touch', title_fontsize=6, prop={'size': 5.5})
leg_cover = fig.legend(handles=cover_handles, loc='center',
                       bbox_to_anchor=(0.5, 0.6), ncol=1, frameon=False,
                       title='Cover', title_fontsize=6, prop={'size': 5.5})
fig.add_artist(leg_touch)

# ── export ────────────────────────────────────────────────────────────────────
for ext in ('pdf', 'png'):
    fig.savefig(f'fig_mr_completeness_all_bars_rotated.{ext}',
                dpi=600, bbox_inches='tight',
                format=ext, transparent=(ext == 'pdf'))
    print(f'Saved fig_mr_completeness_all_bars_rotated.{ext}')

plt.close(fig)