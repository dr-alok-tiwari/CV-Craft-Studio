"""
CV-Craft-Studio - UI Components
Shared Streamlit UI helpers: score cards, gauges, charts, chips, quick actions, etc.
All custom HTML uses explicit colors for maximum dark-mode visibility.
"""

import streamlit as st
import plotly.graph_objects as go
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────────────────

C = {
    'bg_base':   '#FFFDF8',
    'bg_card':   '#FFFFFF',
    'bg_raised': '#FFF4E6',
    'bg_hover':  '#FFE7C2',
    'border':    '#F3D4B0',
    'text':      '#1F2937',
    'text_sec':  '#4B5563',
    'text_muted':'#6B7280',
    'accent':    '#FF9933',
    'teal':      '#E67300',
    'green':     '#15803D',
    'orange':    '#B45309',
    'red':       '#B91C1C',
    'blue':      '#2563EB',
}

PLOTLY_BG    = 'rgba(0,0,0,0)'
PLOTLY_FONT  = {'color': C['text'], 'family': 'Inter, sans-serif'}
PLOTLY_GRID  = 'rgba(180,83,9,0.12)'


def score_color(score: int) -> str:
    """Return hex color for a 0–100 score."""
    try:
        score = int(score)
    except Exception:
        score = 0
    if score >= 80:
        return C['green']
    if score >= 60:
        return '#15803D'
    if score >= 45:
        return C['orange']
    if score >= 30:
        return '#E67E22'
    return C['red']


def score_label(score: int) -> str:
    """Return human-readable label for score."""
    try:
        score = int(score)
    except Exception:
        score = 0
    if score >= 85:
        return 'Excellent'
    if score >= 70:
        return 'Good'
    if score >= 55:
        return 'Average'
    if score >= 40:
        return 'Needs Work'
    return 'Poor'


# ─────────────────────────────────────────────────────────────────────────────
# SCORE GAUGE
# ─────────────────────────────────────────────────────────────────────────────

def render_score_gauge(score: int, title: str = 'ATS Score', max_score: int = 100):
    """Animated gauge chart for a score."""
    color = score_color(score)
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=score,
        title={'text': title, 'font': {'size': 14, 'color': C['text_sec']}},
        number={'font': {'size': 38, 'color': color}, 'suffix': f'/{max_score}'},
        gauge={
            'axis': {
                'range': [0, max_score],
                'tickcolor': C['text_muted'],
                'tickfont': {'color': C['text_muted'], 'size': 10},
            },
            'bar': {'color': color, 'thickness': 0.3},
            'bgcolor': C['bg_raised'],
            'borderwidth': 0,
            'steps': [
                {'range': [0, max_score * 0.4], 'color': 'rgba(185,28,28,0.12)'},
                {'range': [max_score * 0.4, max_score * 0.7], 'color': 'rgba(180,83,9,0.12)'},
                {'range': [max_score * 0.7, max_score], 'color': 'rgba(21,128,61,0.12)'},
            ],
            'threshold': {
                'line': {'color': 'rgba(255,255,255,0.35)', 'width': 2},
                'thickness': 0.75,
                'value': score,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor=PLOTLY_BG,
        plot_bgcolor=PLOTLY_BG,
        font=PLOTLY_FONT,
        height=230,
        margin=dict(t=60, b=10, l=30, r=30),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_score_donut(score: int, title: str = 'Score', size: int = 180):
    """Compact donut for small score displays."""
    score = max(0, min(100, int(score or 0)))
    color = score_color(score)
    fig = go.Figure(data=[go.Pie(
        values=[score, 100 - score],
        hole=0.72,
        marker=dict(colors=[color, '#F6E7D3']),
        showlegend=False,
        textinfo='none',
        hoverinfo='skip',
    )])
    fig.add_annotation(
        text=f'<b>{score}</b>',
        x=0.5,
        y=0.5,
        font=dict(size=26, color=color, family='Inter'),
        showarrow=False,
    )
    fig.update_layout(
        paper_bgcolor=PLOTLY_BG,
        plot_bgcolor=PLOTLY_BG,
        height=size,
        margin=dict(t=5, b=5, l=5, r=5),
        title=dict(text=title, x=0.5, font=dict(size=12, color=C['text_sec'])),
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION SCORE BAR CHART
# ─────────────────────────────────────────────────────────────────────────────

def render_section_scores_chart(sections: Dict):
    """Horizontal bar chart of section scores."""
    if not sections:
        st.info('No section scores available yet.')
        return

    label_map = {
        'contact_info': 'Contact Info',
        'professional_summary': 'Summary',
        'education': 'Education',
        'skills': 'Skills',
        'experience_projects': 'Experience / Projects',
        'action_verbs': 'Action Verbs',
        'quantified_achievements': 'Quantified Results',
        'ats_formatting': 'ATS Formatting',
        'length_readability': 'Length & Readability',
    }
    labels, scores, maxes = [], [], []
    for key, data in sections.items():
        labels.append(label_map.get(key, key.replace('_', ' ').title()))
        scores.append(data.get('score', 0))
        maxes.append(data.get('max', 100))

    pcts = [s / m * 100 if m else 0 for s, m in zip(scores, maxes)]
    colors = [score_color(int(p)) for p in pcts]

    fig = go.Figure(go.Bar(
        x=scores,
        y=labels,
        orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
        text=[f'{s}/{m}' for s, m in zip(scores, maxes)],
        textposition='outside',
        textfont=dict(color=C['text_sec'], size=11),
        hovertemplate='<b>%{y}</b>: %{x}<extra></extra>',
    ))
    fig.update_layout(
        paper_bgcolor=PLOTLY_BG,
        plot_bgcolor=PLOTLY_BG,
        font=PLOTLY_FONT,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, range=[0, max(maxes) + 4]),
        yaxis=dict(showgrid=False, tickfont=dict(size=12, color=C['text'])),
        height=360,
        margin=dict(t=10, b=10, l=10, r=65),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SCORE CARD
# ─────────────────────────────────────────────────────────────────────────────

def render_score_card(title: str, score: int, max_score: int = 100,
                      subtitle: str = '', icon: str = '📊'):
    """Polished metric card with progress bar. All text explicitly colored."""
    score = int(score or 0)
    color = score_color(score / max_score * 100 if max_score else score)
    pct = int(score / max_score * 100) if max_score else 0
    pct = max(0, min(100, pct))
    label = score_label(pct)
    subtitle_html = (
        f'<div style="color:{C["text_muted"]};font-size:10px;margin-top:5px;letter-spacing:0.3px;">{subtitle}</div>'
        if subtitle else ''
    )
    st.markdown(f"""
    <div style="background:{C['bg_card']};
                border-radius:12px; padding:18px 16px; text-align:center;
                border:1px solid {color}2e;
                box-shadow:0 8px 24px rgba(180,83,9,0.08),0 0 0 1px {color}14;
                transition:transform 0.2s;">
        <div style="font-size:26px;margin-bottom:6px;">{icon}</div>
        <div style="color:{C['text_muted']};font-size:10.5px;text-transform:uppercase;
                    letter-spacing:1.2px;font-weight:600;">{title}</div>
        <div style="color:{color};font-size:34px;font-weight:800;
                    margin:8px 0 4px;line-height:1;">
            {score}<span style="font-size:14px;color:{C['text_muted']};font-weight:400;">/{max_score}</span>
        </div>
        <div style="background:{C['bg_base']};border-radius:4px;height:5px;
                    margin:8px 0 6px;overflow:hidden;">
            <div style="background:{color};width:{pct}%;height:100%;border-radius:4px;"></div>
        </div>
        <div style="color:{color};font-size:12px;font-weight:700;">{label}</div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# RED FLAGS
# ─────────────────────────────────────────────────────────────────────────────

def render_red_flag(flag: str, severity: str):
    """Render a single red flag with clear text."""
    cfg = {
        'critical': (C['red'], '🚨', 'rgba(185,28,28,0.10)'),
        'high': (C['orange'], '⚠️', 'rgba(180,83,9,0.10)'),
        'medium': (C['blue'], 'ℹ️', 'rgba(52,152,219,0.10)'),
        'low': (C['green'], '💡', 'rgba(21,128,61,0.10)'),
    }
    color, icon, bg = cfg.get(severity, (C['text_muted'], '•', C['bg_raised']))
    st.markdown(f"""
    <div style="background:{bg};border-left:3px solid {color};
                border-radius:0 8px 8px 0;padding:11px 16px;margin:5px 0;
                display:flex;align-items:center;gap:12px;">
        <span style="font-size:16px;flex-shrink:0;">{icon}</span>
        <span style="color:{C['text']};font-size:13.5px;flex:1;line-height:1.5;">{flag}</span>
        <span style="color:{color};font-size:10px;text-transform:uppercase;
                     font-weight:700;letter-spacing:0.8px;flex-shrink:0;">{severity}</span>
    </div>
    """, unsafe_allow_html=True)


def render_red_flags_list(flags: List[Dict]):
    """Render all red flags sorted by severity."""
    if not flags:
        st.success('✅ No critical red flags detected!')
        return
    for sev in ['critical', 'high', 'medium', 'low']:
        for flag in flags:
            if flag.get('severity') == sev:
                render_red_flag(flag.get('flag', ''), flag.get('severity', sev))


# ─────────────────────────────────────────────────────────────────────────────
# KEYWORD CHIPS
# ─────────────────────────────────────────────────────────────────────────────

def render_keyword_chips(keywords: List[str], color: str = '#FF9933',
                         label: str = 'Keywords'):
    """Render styled keyword chips with visible text."""
    if not keywords:
        return
    chips = ''.join([
        f'<span style="background:{color}1a;color:{color};'
        f'border:1px solid rgba(255,153,51,0.27);border-radius:20px;'
        f'padding:4px 12px;font-size:12.5px;font-weight:500;'
        f'margin:3px 2px;display:inline-block;line-height:1.6;">{kw}</span>'
        for kw in keywords
    ])
    if label:
        st.markdown(f'<div style="color:{C["text_sec"]};font-size:12px;'
                    f'font-weight:600;text-transform:uppercase;letter-spacing:0.8px;'
                    f'margin-bottom:6px;">{label}</div>',
                    unsafe_allow_html=True)
    st.markdown(f'<div style="line-height:2.4;">{chips}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# QUICK ACTION CARD
# ─────────────────────────────────────────────────────────────────────────────

def _quick_action_target(title: str):
    """Map dashboard card titles to the existing sidebar radio labels."""
    return {
        'Upload Resume': ('📤 Upload & Parse Resume', 'Upload & Parse Resume', 'Open Upload'),
        'Build Resume': ('🔨 Resume Builder', 'Resume Builder', 'Open Builder'),
        'Score Resume': ('📊 ATS Resume Scorer', 'ATS Resume Scorer', 'Open Scorer'),
        'Match JD': ('🎯 Job Description Matcher', 'Job Description Matcher', 'Open JD Matcher'),
    }.get(title)


def _navigate_quick_action(nav_value: str, page_name: str):
    """Synchronise the home quick-action button with the sidebar navigation state."""
    st.session_state.current_page = page_name
    st.session_state.nav_radio = nav_value


def _button_key_from_page(page_name: str) -> str:
    safe = page_name.lower().replace(' ', '_').replace('&', 'and').replace('/', '_')
    return f'quick_action_{safe}'


def render_quick_action_card(icon: str, title: str, description: str,
                             color: str = '#FF9933'):
    """Dashboard quick-action card with a real Streamlit navigation button."""
    st.markdown(f"""
    <div style="background:{C['bg_card']};
                border-radius:16px;padding:24px 20px;text-align:center;
                border:1px solid {color}2a;
                box-shadow:0 8px 24px rgba(180,83,9,0.08),0 0 0 1px {color}12;
                transition:transform 0.2s,box-shadow 0.2s;">
        <div style="font-size:38px;margin-bottom:14px;
                    filter:drop-shadow(0 2px 8px rgba(255,153,51,0.30));">{icon}</div>
        <div style="color:{C['text']};font-size:15px;font-weight:700;
                    margin-bottom:8px;letter-spacing:-0.2px;">{title}</div>
        <div style="color:{C['text_sec']};font-size:12.5px;
                    line-height:1.55;min-height:58px;">{description}</div>
        <div style="margin-top:14px;height:2px;border-radius:2px;background:{color}66;"></div>
    </div>
    """, unsafe_allow_html=True)

    target = _quick_action_target(title)
    if target:
        nav_value, page_name, button_label = target
        st.button(
            button_label,
            key=_button_key_from_page(page_name),
            use_container_width=True,
            type='primary',
            on_click=_navigate_quick_action,
            args=(nav_value, page_name),
        )


# ─────────────────────────────────────────────────────────────────────────────
# SUGGESTION BOX
# ─────────────────────────────────────────────────────────────────────────────

def render_suggestion(text: str, severity: str = 'info'):
    """Suggestion / feedback box with explicit text color."""
    cfg = {
        'success': (C['green'], '✅', 'rgba(21,128,61,0.10)', C['green']),
        'warning': (C['orange'], '💡', 'rgba(180,83,9,0.10)', C['orange']),
        'error': (C['red'], '🔴', 'rgba(185,28,28,0.10)', C['red']),
        'info': (C['blue'], 'ℹ️', 'rgba(52,152,219,0.10)', C['blue']),
    }
    border_color, icon, bg, text_color = cfg.get(severity, cfg['info'])
    st.markdown(f"""
    <div style="background:{bg};border-left:3px solid {border_color};
                border-radius:0 8px 8px 0;padding:11px 16px;margin:5px 0;">
        <span style="color:{text_color};font-size:13.5px;
                     line-height:1.55;">{icon}&nbsp; {text}</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS BAR
# ─────────────────────────────────────────────────────────────────────────────

def render_progress_bar(value: float, label: str = '', color: str = '#FF9933'):
    """Custom animated progress bar."""
    pct = min(100, max(0, float(value or 0)))
    label_html = (
        f'<div style="color:{C["text_sec"]};font-size:12.5px;font-weight:500;margin-bottom:5px;">{label}</div>'
        if label else ''
    )
    st.markdown(f"""
    <div style="margin:6px 0 14px;">
        {label_html}
        <div style="background:{C['bg_raised']};border-radius:6px;
                    height:9px;overflow:hidden;border:1px solid {C['border']};">
            <div style="background:{color};width:{pct}%;height:100%;border-radius:6px;
                        transition:width 0.6s ease;
                        box-shadow:0 0 8px rgba(255,153,51,0.27);"></div>
        </div>
        <div style="color:{C['text_muted']};font-size:11px;
                    margin-top:3px;text-align:right;font-weight:500;">{pct:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# JD MATCH PIE CHART
# ─────────────────────────────────────────────────────────────────────────────

def render_jd_match_chart(matched: int, missing: int, title: str = 'Match'):
    """Donut chart for keyword match results."""
    matched = max(0, int(matched or 0))
    missing = max(0, int(missing or 0))
    if matched + missing == 0:
        missing = 1
    fig = go.Figure(data=[go.Pie(
        labels=['Matched', 'Missing'],
        values=[matched, missing],
        hole=0.55,
        marker=dict(colors=[C['green'], '#F6E7D3']),
        textinfo='label+percent',
        textfont=dict(color=C['text'], size=12, family='Inter'),
        hovertemplate='<b>%{label}</b>: %{value}<extra></extra>',
        pull=[0.03, 0],
    )])
    fig.update_layout(
        paper_bgcolor=PLOTLY_BG,
        plot_bgcolor=PLOTLY_BG,
        font=PLOTLY_FONT,
        title=dict(text=title, x=0.5, font=dict(size=14, color=C['text_sec'])),
        height=250,
        margin=dict(t=40, b=10, l=10, r=10),
        legend=dict(font=dict(color=C['text']), bgcolor='rgba(0,0,0,0)'),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# STAT ROW (horizontal metrics strip)
# ─────────────────────────────────────────────────────────────────────────────

def render_stat_row(stats: List[Dict]):
    """Render a horizontal strip of stat tiles."""
    if not stats:
        return
    cols = st.columns(len(stats))
    for col, stat in zip(cols, stats):
        color = stat.get('color', C['accent'])
        with col:
            st.markdown(f"""
            <div style="background:{C['bg_card']};border:1px solid {C['border']};
                        border-radius:10px;padding:14px 12px;text-align:center;">
                <div style="font-size:22px;margin-bottom:4px;">{stat.get('icon','📊')}</div>
                <div style="color:{color};font-size:22px;font-weight:800;line-height:1;">{stat['value']}</div>
                <div style="color:{C['text_muted']};font-size:11px;
                            margin-top:4px;text-transform:uppercase;
                            letter-spacing:0.7px;">{stat['label']}</div>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION HEADER
# ─────────────────────────────────────────────────────────────────────────────

def render_section_header(title: str, subtitle: str = '', icon: str = ''):
    """Styled section header with optional subtitle."""
    icon_html = f'<span style="font-size:20px;">{icon}</span>' if icon else ''
    subtitle_html = f'<div style="color:{C["text_muted"]};font-size:12.5px;margin-top:3px;">{subtitle}</div>' if subtitle else ''
    st.markdown(f"""
    <div style="margin:24px 0 14px;">
        <div style="display:flex;align-items:center;gap:8px;">
            {icon_html}
            <span style="color:{C['text']};font-size:18px;font-weight:700;
                         letter-spacing:-0.3px;">{title}</span>
        </div>
        {subtitle_html}
        <div style="height:1px;background:rgba(255,153,51,0.33);margin-top:8px;"></div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# INFO BANNER
# ─────────────────────────────────────────────────────────────────────────────

def render_info_banner(text: str, color: str = '#FF9933', icon: str = 'ℹ️'):
    """Subtle full-width info banner."""
    st.markdown(f"""
    <div style="background:rgba(255,153,51,0.07);border:1px solid rgba(255,153,51,0.20);
                border-radius:10px;padding:12px 18px;margin:8px 0;
                display:flex;align-items:center;gap:12px;">
        <span style="font-size:18px;">{icon}</span>
        <span style="color:{C['text']};font-size:13.5px;line-height:1.5;">{text}</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE BADGE
# ─────────────────────────────────────────────────────────────────────────────

def render_feature_badge(label: str, is_new: bool = False):
    """Small badge for new/beta features."""
    color = C['green'] if is_new else C['teal']
    text = '✨ NEW' if is_new else 'BETA'
    st.markdown(
        f'<span style="background:rgba(255,153,51,0.13);color:{color};border:1px solid rgba(255,153,51,0.27);'
        f'border-radius:20px;padding:2px 9px;font-size:10px;font-weight:700;'
        f'letter-spacing:0.5px;">{text}: {label}</span>',
        unsafe_allow_html=True,
    )
