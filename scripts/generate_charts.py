import os
import matplotlib.pyplot as plt
import numpy as np

os.makedirs("docs/charts", exist_ok=True)

# Common styling
plt.style.use('dark_background')
bg_color = '#121813'
card_color = '#1a221b'
accent_green = '#a8d5a2'
bright_green = '#4ade80'
subtle_gray = '#94a3b8'
border_color = '#2e3b30'

# 1. Latency Breakdown
def generate_latency_chart():
    categories = ['Direct Clock', 'Doc Similarity', 'Doc Spread', 'DuckDuckGo Web', 'Hybrid Fallback']
    ttft = [45, 180, 240, 420, 610]
    gen_time = [65, 380, 520, 490, 680]

    x = np.arange(len(categories))
    width = 0.55

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=bg_color)
    ax.set_facecolor(card_color)

    p1 = ax.bar(x, ttft, width, label='Time to First Token (TTFT)', color=accent_green, edgecolor=border_color)
    p2 = ax.bar(x, gen_time, width, bottom=ttft, label='Full Token Stream Generation', color='#2dd4bf', edgecolor=border_color)

    ax.set_ylabel('Latency (Milliseconds)', fontsize=11, color='#e2e8f0', fontweight='medium')
    ax.set_title('End-to-End Latency by Query Routing Path', fontsize=13, color='#f8fafc', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=10, color='#cbd5e1')
    ax.legend(facecolor=card_color, edgecolor=border_color, fontsize=9.5, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.25, color=subtle_gray)

    for i in range(len(categories)):
        total = ttft[i] + gen_time[i]
        ax.annotate(f'{total}ms', (x[i], total + 25), ha='center', va='bottom', fontsize=9.5, color='#f1f5f9', fontweight='bold')

    ax.set_ylim(0, 1500)
    for spine in ax.spines.values():
        spine.set_color(border_color)

    plt.tight_layout()
    plt.savefig('docs/charts/latency_breakdown.png', dpi=300, facecolor=bg_color)
    plt.close()
    print("Chart 1: latency_breakdown.png generated.")

# 2. Cosine Similarity Distribution
def generate_similarity_chart():
    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=bg_color)
    ax.set_facecolor(card_color)

    x = np.linspace(-0.2, 1.0, 500)
    
    # Gaussian curves for three regimes
    def gaussian(x, mu, sig):
        return np.exp(-np.power(x - mu, 2.) / (2 * np.power(sig, 2.)))

    irrelevant = gaussian(x, 0.12, 0.08) * 0.9
    borderline = gaussian(x, 0.38, 0.06) * 0.6
    relevant = gaussian(x, 0.65, 0.10) * 1.0

    ax.plot(x, irrelevant, label='Out-of-Domain / Irrelevant Chunks', color='#f43f5e', linewidth=2)
    ax.fill_between(x, irrelevant, alpha=0.2, color='#f43f5e')

    ax.plot(x, borderline, label='Contextually Borderline Chunks', color='#fbbf24', linewidth=2)
    ax.fill_between(x, borderline, alpha=0.2, color='#fbbf24')

    ax.plot(x, relevant, label='Grounded Document Matches', color=bright_green, linewidth=2)
    ax.fill_between(x, relevant, alpha=0.2, color=bright_green)

    # Threshold line
    ax.axvline(0.35, color='#38bdf8', linestyle='--', linewidth=2, label='Routing Cutoff (tau = 0.35)')
    
    ax.annotate('Rejection & Web Fallback\n(Score < 0.35)', xy=(0.33, 0.8), xytext=(0.02, 0.82),
                arrowprops=dict(facecolor='#f43f5e', shrink=0.08, width=1.5, headwidth=6),
                fontsize=9.5, color='#fecdd3', fontweight='medium', ha='center',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#881337', edgecolor='#f43f5e', alpha=0.8))

    ax.annotate('Accept & Ground Answer\n(Score >= 0.35)', xy=(0.37, 0.8), xytext=(0.68, 0.82),
                arrowprops=dict(facecolor=bright_green, shrink=0.08, width=1.5, headwidth=6),
                fontsize=9.5, color='#dcfce7', fontweight='medium', ha='center',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#14532d', edgecolor=bright_green, alpha=0.8))

    ax.set_title('Cosine Similarity Distribution & Dynamic Routing Threshold', fontsize=13, color='#f8fafc', fontweight='bold', pad=15)
    ax.set_xlabel('Cosine Similarity Score (1.0 - Distance)', fontsize=11, color='#e2e8f0')
    ax.set_ylabel('Probability Density (Arbitrary Units)', fontsize=11, color='#e2e8f0')
    ax.set_xlim(-0.1, 0.95)
    ax.set_ylim(0, 1.15)
    ax.legend(facecolor=card_color, edgecolor=border_color, fontsize=9, loc='upper left')
    ax.grid(axis='both', linestyle='--', alpha=0.2, color=subtle_gray)

    for spine in ax.spines.values():
        spine.set_color(border_color)

    plt.tight_layout()
    plt.savefig('docs/charts/cosine_similarity_distribution.png', dpi=300, facecolor=bg_color)
    plt.close()
    print("Chart 2: cosine_similarity_distribution.png generated.")

# 3. Model Hardware Matrix
def generate_hardware_matrix():
    models = ['qwen3-embed\n(0.6B)', 'llama3.2\n(3B)', 'qwen2.5-coder\n(7B - Default)', 'qwen2.5-coder\n(14B)']
    vram = [0.6, 2.5, 5.0, 9.2]
    rec_spec = [2, 6, 8, 16]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor=bg_color)
    ax.set_facecolor(card_color)

    r1 = ax.bar(x - width/2, vram, width, label='Model Working VRAM/RAM (GB)', color='#38bdf8', edgecolor=border_color)
    r2 = ax.bar(x + width/2, rec_spec, width, label='Minimum Host Memory Target (GB)', color=accent_green, edgecolor=border_color)

    ax.set_ylabel('Memory (Gigabytes)', fontsize=11, color='#e2e8f0', fontweight='medium')
    ax.set_title('Ollama Model Parameters vs. Hardware Memory Allocation', fontsize=13, color='#f8fafc', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10, color='#cbd5e1')
    ax.legend(facecolor=card_color, edgecolor=border_color, fontsize=9.5, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.25, color=subtle_gray)

    for bar in r1:
        h = bar.get_height()
        ax.annotate(f'{h} GB', (bar.get_x() + bar.get_width()/2, h + 0.3), ha='center', va='bottom', fontsize=9, color='#bae6fd', fontweight='bold')

    for bar in r2:
        h = bar.get_height()
        ax.annotate(f'{h} GB', (bar.get_x() + bar.get_width()/2, h + 0.3), ha='center', va='bottom', fontsize=9, color='#dcfce7', fontweight='bold')

    ax.set_ylim(0, 18)
    for spine in ax.spines.values():
        spine.set_color(border_color)

    plt.tight_layout()
    plt.savefig('docs/charts/model_hardware_matrix.png', dpi=300, facecolor=bg_color)
    plt.close()
    print("Chart 3: model_hardware_matrix.png generated.")

# 4. Voice Pipeline Waterfall
def generate_voice_waterfall():
    stages = [
        '1. Browser Mic Capture',
        '2. WAV Upload & Staging',
        '3. Faster-Whisper STT',
        '4. RAG Context Retrieval',
        '5. LLM First Token (TTFT)',
        '6. Edge-TTS Audio Synth',
        '7. Web Audio Playback'
    ]
    durations = [40, 25, 380, 110, 185, 220, 30]
    
    cumulative = [0]
    for d in durations[:-1]:
        cumulative.append(cumulative[-1] + d)

    total_time = sum(durations)

    fig, ax = plt.subplots(figsize=(8.5, 4.8), facecolor=bg_color)
    ax.set_facecolor(card_color)

    y_pos = np.arange(len(stages))
    ax.barh(y_pos, durations, left=cumulative, height=0.55, color='#34d399', edgecolor=border_color, alpha=0.9)

    for i in range(len(stages)):
        start = cumulative[i]
        dur = durations[i]
        ax.text(start + dur/2, i, f'{dur}ms', ha='center', va='center', color='#022c22', fontweight='bold', fontsize=9)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(stages, fontsize=10, color='#e2e8f0')
    ax.invert_yaxis()
    ax.set_xlabel('Cumulative Latency Timeline (Milliseconds)', fontsize=11, color='#e2e8f0', labelpad=10)
    ax.set_title(f'Bidirectional Voice Pipeline: Stage Latencies (Total: {total_time}ms)', fontsize=13, color='#f8fafc', fontweight='bold', pad=15)
    ax.axvline(total_time, color='#f43f5e', linestyle='--', linewidth=1.5, label=f'Turnaround Target < 1000ms ({total_time}ms)')
    ax.legend(facecolor=card_color, edgecolor=border_color, fontsize=9.5, loc='lower right')
    ax.grid(axis='x', linestyle='--', alpha=0.25, color=subtle_gray)
    ax.set_xlim(0, 1150)

    for spine in ax.spines.values():
        spine.set_color(border_color)

    plt.tight_layout()
    plt.savefig('docs/charts/voice_pipeline_waterfall.png', dpi=300, facecolor=bg_color)
    plt.close()
    print("Chart 4: voice_pipeline_waterfall.png generated.")

# 5. Provider Throughput & Cost Comparison
def generate_provider_throughput():
    providers = ['Ollama CPU\n(llama3.2:3b)', 'Ollama GPU\n(qwen2.5:7b)', 'OpenAI Cloud\n(gpt-4o-mini)', 'Gemini Cloud\n(gemini-2.0-flash)']
    throughput = [19, 48, 82, 96]
    cost_per_million = [0.0, 0.0, 0.15, 0.10]

    x = np.arange(len(providers))
    width = 0.55

    fig, ax1 = plt.subplots(figsize=(8, 4.5), facecolor=bg_color)
    ax1.set_facecolor(card_color)

    bars = ax1.bar(x, throughput, width, color='#38bdf8', edgecolor=border_color, label='Generation Speed (Tokens / Sec)')
    ax1.set_ylabel('Speed (Tokens / Second)', color='#38bdf8', fontsize=11, fontweight='medium')
    ax1.tick_params(axis='y', labelcolor='#38bdf8')
    ax1.set_xticks(x)
    ax1.set_xticklabels(providers, fontsize=10, color='#e2e8f0')
    ax1.set_ylim(0, 120)

    for bar in bars:
        h = bar.get_height()
        ax1.annotate(f'{h} tps', (bar.get_x() + bar.get_width()/2, h + 2.5), ha='center', va='bottom', fontsize=9.5, color='#bae6fd', fontweight='bold')

    # Line for cost
    ax2 = ax1.twinx()
    ax2.plot(x, cost_per_million, color='#fbbf24', marker='o', linewidth=2.5, markersize=8, label='Inference Cost ($ / 1M tokens)')
    ax2.set_ylabel('Inference Cost ($ per 1M Tokens)', color='#fbbf24', fontsize=11, fontweight='medium')
    ax2.tick_params(axis='y', labelcolor='#fbbf24')
    ax2.set_ylim(-0.02, 0.25)

    for i, c in enumerate(cost_per_million):
        ax2.annotate(f'${c:.2f}', (x[i], c + 0.015), ha='center', va='bottom', fontsize=9.5, color='#fef08a', fontweight='bold')

    ax1.set_title('Inference Throughput vs. Operational Cost Across Providers', fontsize=13, color='#f8fafc', fontweight='bold', pad=15)
    ax1.grid(axis='y', linestyle='--', alpha=0.2, color=subtle_gray)

    for spine in ax1.spines.values():
        spine.set_color(border_color)

    plt.tight_layout()
    plt.savefig('docs/charts/provider_throughput_comparison.png', dpi=300, facecolor=bg_color)
    plt.close()
    print("Chart 5: provider_throughput_comparison.png generated.")

if __name__ == '__main__':
    generate_latency_chart()
    generate_similarity_chart()
    generate_hardware_matrix()
    generate_voice_waterfall()
    generate_provider_throughput()
    print("All 5 metric charts successfully created in docs/charts/")
