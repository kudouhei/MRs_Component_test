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
    'font.size':          9,
    'axes.titlesize':     9.5,
    'axes.labelsize':     9,
    'xtick.labelsize':    8.5,
    'ytick.labelsize':    8.5,
    'legend.fontsize':    6.5,
    'axes.linewidth':     0.6,
    'axes.spines.top':    False,
    'axes.spines.right':  False,
    'xtick.major.width':  0.6,
    'ytick.major.width':  0.6,
    'xtick.direction':    'out',
    'ytick.direction':    'out',
    'grid.linewidth':     0.4,
    'grid.alpha':         0.45,
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
fig, axes = plt.subplots(1, 2, figsize=(7.16, 3.0))
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

    # 在每个 x 位置标注 Touch 组和 Cover 组的最大/最小 bar
    for j in range(n):
        # Touch 组
        touch_keys = ['T_gem', 'T_deep', 'T_gpt']
        touch_vals = {k: data[k][j] for k in touch_keys}
        max_key = max(touch_vals, key=touch_vals.get)
        min_key = min(touch_vals, key=touch_vals.get)
        # 最大值（粗体）
        rect_max = bars[max_key][j]
        ax.text(rect_max.get_x() + rect_max.get_width()/2., rect_max.get_height() + 1.2,
                f'{touch_vals[max_key]:.1f}', ha='center', va='bottom',
                fontsize=5, color='black', weight='bold')
        # 最小值（如果与最大值不同）
        if max_key != min_key:
            rect_min = bars[min_key][j]
            ax.text(rect_min.get_x() + rect_min.get_width()/2., rect_min.get_height() + 1.2,
                    f'{touch_vals[min_key]:.1f}', ha='center', va='bottom',
                    fontsize=5, color='black', weight='normal')
        # Cover 组
        cover_keys = ['C_gem', 'C_deep', 'C_gpt']
        cover_vals = {k: data[k][j] for k in cover_keys}
        max_key_c = max(cover_vals, key=cover_vals.get)
        min_key_c = min(cover_vals, key=cover_vals.get)
        rect_max_c = bars[max_key_c][j]
        ax.text(rect_max_c.get_x() + rect_max_c.get_width()/2., rect_max_c.get_height() + 1.2,
                f'{cover_vals[max_key_c]:.1f}', ha='center', va='bottom',
                fontsize=5, color='black', weight='bold')
        if max_key_c != min_key_c:
            rect_min_c = bars[min_key_c][j]
            ax.text(rect_min_c.get_x() + rect_min_c.get_width()/2., rect_min_c.get_height() + 1.2,
                    f'{cover_vals[min_key_c]:.1f}', ha='center', va='bottom',
                    fontsize=5, color='black', weight='normal')

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=6.5)
    ax.set_ylim(0, 104)   # 为标签留空间
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{int(v)}%'))
    ax.yaxis.grid(True, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title(subtitle, fontsize=9.5, fontweight='bold', pad=6, loc='left')

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
                       bbox_to_anchor=(0.5, 0.63), ncol=1, frameon=False,
                       title='Touch', title_fontsize=8, prop={'size': 6})
leg_cover = fig.legend(handles=cover_handles, loc='center',
                       bbox_to_anchor=(0.5, 0.37), ncol=1, frameon=False,
                       title='Cover', title_fontsize=8, prop={'size': 6})
fig.add_artist(leg_touch)

# ── export ────────────────────────────────────────────────────────────────────
for ext in ('pdf', 'png'):
    fig.savefig(f'fig_mr_completeness_minmax_bar.{ext}',
                dpi=300, bbox_inches='tight',
                format=ext, transparent=(ext == 'pdf'))
    print(f'Saved fig_mr_completeness_minmax_bar.{ext}')

plt.close(fig)