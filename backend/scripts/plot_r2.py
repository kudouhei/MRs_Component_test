import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 8,
    'axes.labelsize': 8,
    'axes.titlesize': 8.5,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'legend.fontsize': 7,
    'axes.linewidth': 0.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
})

llms = ['DeepSeek', 'Gemini', 'GPT']
cover = np.array([44.6, 47.6, 42.5])
weak = np.array([36.0, 39.9, 40.4])
untouched = np.array([19.4, 12.5, 17.1])
colors = ['#3266ad', '#7da4ce', '#e89878']

# 水平堆叠
y = np.arange(len(llms))
bar_height = 0.5                    # 横条高度
fig, ax = plt.subplots(figsize=(3.0, 1.6))   # 宽度稍宽，高度很矮

bars1 = ax.barh(y, cover, bar_height, color=colors[0], label='Cover')
bars2 = ax.barh(y, weak, bar_height, left=cover, color=colors[1], label='Weak')
bars3 = ax.barh(y, untouched, bar_height, left=cover+weak, color=colors[2], label='Untouched')

# 数值标签
def annotate_h(vals, lefts):
    for i in range(len(vals)):
        if vals[i] < 5:
            continue
        x_center = lefts[i] + vals[i] / 2
        ax.text(x_center, y[i], f'{vals[i]:.1f}', ha='center', va='center',
                fontsize=6.0, color='white', weight='bold')

annotate_h(cover, np.zeros_like(cover))
annotate_h(weak, cover)
annotate_h(untouched, cover + weak)

ax.set_yticks(y)
ax.set_yticklabels(llms)
ax.set_xlabel('Percentage (%)')
ax.set_xlim(0, 100)
ax.set_xticks(np.arange(0, 101, 20))
ax.grid(axis='x', linestyle=':', linewidth=0.4, alpha=0.35)
ax.set_axisbelow(True)

ax.legend(ncol=3, frameon=False, loc='upper center',
          bbox_to_anchor=(0.5, 1.25), columnspacing=1.0, handlelength=1.0)

plt.subplots_adjust(top=0.85)
plt.tight_layout()
plt.savefig('stacked_mr_outcomes_horizontal.pdf', bbox_inches='tight')
plt.savefig('stacked_mr_outcomes_horizontal.png', dpi=300, bbox_inches='tight')
plt.close()