"""
Report generator module for creating email reports from issue analysis.

This module generates HTML and plain text email reports with WWWH-TR analysis.
"""

import html
from typing import Any, Dict

# Label color mapping
LABEL_COLORS = {
    "UNIOSS 3": "rgb(143, 188, 143)",
    "改修依頼": "rgb(230, 230, 250)",
    "優先度 高": "rgb(194, 30, 86)",
    "(報告)判断待ち": "rgb(0, 0, 255)",
    "UNIOSS 2": "rgb(230, 230, 250)",
    "UNIOSS 3 移行後対応": "rgb(148, 0, 211)",
    "unitTest": "rgb(230, 230, 250)",
    "おとどけ丸": "rgb(237, 145, 33)",
    "さくら市": "rgb(230, 230, 250)",
    "さぬき市": "rgb(230, 230, 250)",
    "データ補正": "rgb(128, 128, 128)",
    "ビオプラス": "rgb(102, 153, 204)",
    "ビオプラス 要望": "rgb(0, 153, 102)",
    "リファクタ": "rgb(238, 230, 0)",
    "安中市": "rgb(230, 230, 250)",
    "印南町": "rgb(102, 153, 204)",
    "宇部市": "rgb(230, 230, 250)",
    "下野市": "rgb(230, 230, 250)",
    "笠岡市": "rgb(230, 230, 250)",
    "菊川市": "rgb(230, 230, 250)",
    "宮崎市": "rgb(230, 230, 250)",
    "桑名市": "rgb(230, 230, 250)",
    "君津市": "rgb(230, 230, 250)",
    "芸西村": "rgb(230, 230, 250)",
    "鍵和田": "rgb(102, 153, 204)",
    "御嵩町": "rgb(230, 230, 250)",
    "御殿場市": "rgb(230, 230, 250)",
    "最優先": ["rgb(220, 20, 60)", "rgb(148, 0, 211)"],
    "三好市": "rgb(230, 230, 250)",
    "三朝町": "rgb(230, 230, 250)",
    "仕様検討中": "rgb(230, 230, 250)",
    "滋賀県甲賀市": "rgb(102, 153, 204)",
    "自治体移行作業": "rgb(102, 153, 204)",
    "自販機": "rgb(195, 153, 83)",
    "鹿沼市": "rgb(230, 230, 250)",
    "七尾市": "rgb(230, 230, 250)",
    "七尾市(寄附金)": "rgb(230, 230, 250)",
    "修正確認待ち": "rgb(0, 0, 255)",
    "小矢部市": "rgb(230, 230, 250)",
    "松田町": "rgb(230, 230, 250)",
    "沼津市": "rgb(230, 230, 250)",
    "上富田町": "rgb(230, 230, 250)",
    "城崎": "rgb(102, 153, 204)",
    "城里町": "rgb(230, 230, 250)",
    "常総市": "rgb(230, 230, 250)",
    "新潟県庁": "rgb(102, 153, 204)",
    "新規自治体": "rgb(230, 230, 250)",
    "新規実装": "rgb(230, 230, 250)",
    "真岡市": "rgb(230, 230, 250)",
    "請求・帳票の再構築": "rgb(255, 235, 205)",
    "石狩市": "rgb(230, 230, 250)",
    "川場村": "rgb(230, 230, 250)",
    "泉佐野市": "rgb(230, 230, 250)",
    "泉南市": "rgb(230, 230, 250)",
    "相模原市": "rgb(230, 230, 250)",
    "対応完了": "rgb(0, 136, 255)",
    "対応中": "rgb(255, 0, 0)",
    "大玉村": "rgb(230, 230, 250)",
    "大村市": "rgb(230, 230, 250)",
    "大網白里市": "rgb(230, 230, 250)",
    "丹波篠山市": "rgb(230, 230, 250)",
    "中井町": "rgb(230, 230, 250)",
    "朝来市": "rgb(230, 230, 250)",
    "長泉町": "rgb(230, 230, 250)",
    "長野原町": "rgb(230, 230, 250)",
    "辻岡": "rgb(102, 153, 204)",
    "登別市": "rgb(230, 230, 250)",
    "東伊豆町": "rgb(230, 230, 250)",
    "湯河原町": "rgb(230, 230, 250)",
    "徳島県三好市": "rgb(102, 153, 204)",
    "那須町": "rgb(230, 230, 250)",
    "白老町": "rgb(237, 145, 33)",
    "美作市": "rgb(237, 145, 33)",
    "不具合": "rgb(230, 230, 250)",
    "富士市": "rgb(230, 230, 250)",
    "富田林市": "rgb(230, 230, 250)",
    "福井市": "rgb(230, 230, 250)",
    "福岡県小郡市": "rgb(102, 153, 204)",
    "宝塚市": "rgb(230, 230, 250)",
    "優先度 中": "rgb(237, 145, 33)",
    "優先度 低": "rgb(102, 153, 204)",
    "竜王町": "rgb(230, 230, 250)",
    "和歌山県印南町": "rgb(102, 153, 204)",
}


def get_label_color(label_name: str) -> str:
    """
    Get the color for a label from the mapping.
    
    Args:
        label_name: Name of the label
        
    Returns:
        Color string (RGB format) or default color if not found
    """
    color = LABEL_COLORS.get(label_name)
    if color is None:
        # Default color if label not in mapping
        return "rgb(155, 155, 155)"
    
    # Handle array colors (use first color)
    if isinstance(color, list):
        return color[0]
    
    return color


def get_text_color_for_background(bg_color: str) -> str:
    """
    Determine appropriate text color (black or white) based on background color brightness.
    
    Args:
        bg_color: Background color in RGB format (e.g., "rgb(230, 230, 250)")
        
    Returns:
        Text color string ("#000000" for light backgrounds, "#ffffff" for dark backgrounds)
    """
    import re
    
    # Extract RGB values from "rgb(r, g, b)" format
    match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", bg_color)
    if not match:
        # Default to white if format is unexpected
        return "#ffffff"
    
    r, g, b = int(match.group(1)), int(match.group(2)), int(match.group(3))
    
    # Calculate relative luminance (simplified formula)
    # Using standard formula: 0.299*R + 0.587*G + 0.114*B
    brightness = (0.299 * r + 0.587 * g + 0.114 * b)
    
    # Use black text for light backgrounds (brightness > 128), white for dark
    return "#000000" if brightness > 128 else "#ffffff"

# Fixed HTML template for AI to fill in
FIXED_HTML_TEMPLATE = """<div class="rcmBody" id="message-htmlpart1" style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5">
    <table style="width: 100%; background-color: #f5f5f5">
        <tbody><tr>
            <td>
                <table style="width: 100%; max-width: 800px; margin: 0 auto; background-color: #ffffff;">
                    <tbody><tr>
                        <td>
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="font-family: Arial, sans-serif; color: #333; max-width: 1200px; margin: auto">
    <tbody><tr>
        <td>

            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #f0f7ff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #4a90e2">
                <tbody><tr>
                    <td>
                        <div style="font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 12px">{ISSUE_TITLE}</div>
                        <div style="margin-top: 12px; font-size: 14px; line-height: 1.8">
                            <div style="margin-bottom: 8px">
                                <span style="font-weight: 600; color: #555; margin-right: 8px">Status:</span>
                                <span style="display: inline-block; background-color: {ISSUE_STATE_COLOR}; color: #ffffff; padding: 4px 12px; border-radius: 16px; font-size: 12px;">{ISSUE_STATE}</span>
                            </div>
                            <div style="margin-bottom: 8px">
                                <span style="font-weight: 600; color: #555; margin-right: 8px">Priority:</span>
                                <span style="display: inline-block; background-color: #f39c12; color: #ffffff; padding: 4px 12px; border-radius: 16px; font-size: 12px;">{ISSUE_PRIORITY}</span>
                            </div>
                            <div style="margin-bottom: 8px">
                                <span style="font-weight: 600; color: #555; margin-right: 8px">Estimation:</span>
                                <span style="display: inline-block; background-color: #9b59b6; color: #ffffff; padding: 4px 12px; border-radius: 16px; font-size: 12px;">{ESTIMATION}</span>
                            </div>
                            <div style="margin-bottom: 8px">
                                <span style="font-weight: 600; color: #555; margin-right: 8px">Labels:</span>
                                {ISSUE_LABELS}
                            </div>
                        </div>
                        <div style="margin-top: 12px; font-size: 14px; padding-top: 12px; border-top: 1px solid #d0e0f0">
                            <strong style="color: #555">Creator:</strong> <span style="color: #333">{ISSUE_AUTHOR}</span> &nbsp;|&nbsp; <strong style="color: #555">Assignee:</strong> <span style="color: #333">{ISSUE_ASSIGNEE}</span>
                        </div>
                        <div style="margin-top: 8px; font-size: 14px">
                            <strong style="color: #555">URL:</strong> <a href="{ISSUE_URL}" style="color: #4a90e2; text-decoration: none" target="_blank" rel="noreferrer">{ISSUE_URL}</a>
                        </div>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #f39c12">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">📌 TL;DR</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {TLDR_ITEMS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #27ae60">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">✅ Action Items</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {ACTION_ITEMS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #e74c3c">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">❓ Open Questions</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {OPEN_QUESTIONS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #9b59b6">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">W1 — Why</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {W1_ITEMS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #3498db">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">W2 — What</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {W2_ITEMS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #e67e22">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">W3 — Who</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {W3_ITEMS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #1abc9c">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">H — How</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {H_ITEMS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #f1c40f">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">T — Test</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {T_ITEMS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>


            <table width="100%" cellpadding="15" cellspacing="0" border="0" style="background-color: #fff; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #7f8c8d">
                <tbody><tr>
                    <td>
                        <div style="font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px">R — Reflect</div>
                        <ul style="margin: 0; padding-left: 20px; font-size: 14px; line-height: 1.6">
                            {R_ITEMS}
                        </ul>
                    </td>
                </tr>
            </tbody></table>



        </td>
    </tr>
</tbody></table>
                        </td>
                    </tr>
                </tbody></table>
            </td>
        </tr>
    </tbody></table>
</div>"""


def get_fixed_html_template(issue_data: Dict[str, Any]) -> str:
    """
    Get the fixed HTML template with issue metadata filled in.
    Only the analysis sections remain as placeholders for AI to fill.

    Args:
        issue_data: Issue data dictionary

    Returns:
        HTML template string with issue metadata filled, analysis placeholders remaining
    """
    # Extract issue information
    title = issue_data.get("title", "Untitled Issue")
    url = issue_data.get("web_url") or issue_data.get("url", "#")
    state = issue_data.get("state", "unknown")
    
    # Get status badge color - use #52b87a for "open" state
    state_lower = str(state).lower()
    if state_lower == "opened" or state_lower == "open":
        status_color = "#52b87a"
    else:
        # Default color for other states (closed, etc.)
        status_color = "#4a90e2"

    # Format priority
    priority = issue_data.get("priority", "not set")
    if isinstance(priority, dict):
        priority = priority.get("name", "not set")

    # Format labels as rounded badges with color mapping
    labels = issue_data.get("labels", [])
    labels_html = ""
    if labels:
        labels_badges = []
        for label in labels:
            label_name = (
                label.get("name", label) if isinstance(label, dict) else str(label)
            )
            # Get color from mapping
            label_color = get_label_color(str(label_name))
            # Determine text color based on background brightness
            text_color = get_text_color_for_background(label_color)
            
            # Create rounded badge for each label
            label_escaped = html.escape(str(label_name))
            labels_badges.append(
                f'<span style="display: inline-block; background-color: {label_color}; color: {text_color}; padding: 4px 12px; border-radius: 16px; font-size: 12px; margin-right: 6px; margin-bottom: 4px">{label_escaped}</span>'
            )
        labels_html = "".join(labels_badges)
    else:
        labels_html = '<span style="display: inline-block; background-color: #95a5a6; color: #ffffff; padding: 4px 12px; border-radius: 16px; font-size: 12px; font-style: italic">None</span>'

    # Format assignee
    assignee = issue_data.get("assignee")
    if isinstance(assignee, dict):
        assignee_str = assignee.get("username", assignee.get("name", "Unassigned"))
    elif assignee:
        assignee_str = str(assignee)
    else:
        assignee_str = "Unassigned"

    # Format author
    author = issue_data.get("author")
    if isinstance(author, dict):
        author_str = author.get("username", author.get("name", "Unknown"))
    elif author:
        author_str = str(author)
    else:
        author_str = "Unknown"

    # Fill in issue metadata, leave analysis sections as placeholders
    template = FIXED_HTML_TEMPLATE.replace("{ISSUE_TITLE}", html.escape(title))
    template = template.replace("{ISSUE_STATE}", html.escape(str(state)))
    template = template.replace("{ISSUE_STATE_COLOR}", status_color)
    template = template.replace("{ISSUE_PRIORITY}", html.escape(str(priority)))
    template = template.replace("{ESTIMATION}", "{{ESTIMATION}}")  # Placeholder for AI to fill
    template = template.replace("{ISSUE_LABELS}", labels_html)  # Already HTML formatted
    template = template.replace("{ISSUE_URL}", html.escape(url))
    template = template.replace("{ISSUE_AUTHOR}", html.escape(author_str))
    template = template.replace("{ISSUE_ASSIGNEE}", html.escape(assignee_str))

    return template


def generate_email_report(
    issue_data: Dict[str, Any],
    analysis: Dict[str, Any],
    subject_prefix: str = "[GitLab Issue Analysis]",
) -> Dict[str, str]:
    """
    Generate email report with HTML and plain text versions.

    Args:
        issue_data: Issue data dictionary
        analysis: Analysis dictionary with 'html' (AI-generated HTML) and 'raw' (raw content)
        subject_prefix: Prefix for email subject

    Returns:
        Dictionary with:
        - 'subject': Email subject line
        - 'html': HTML email body
        - 'text': Plain text email body
    """
    # Generate subject with issue ID
    issue_iid = issue_data.get("iid") or issue_data.get("id")
    title = issue_data.get("title", "Untitled Issue")
    if issue_iid:
        subject = f"{subject_prefix} #{issue_iid}: {title}"
    else:
        subject = f"{subject_prefix} {title}"

    # Use AI-generated HTML if available, otherwise fallback to formatted version
    ai_html = analysis.get("html", "")

    if ai_html:
        # Use AI-generated HTML directly (already wrapped in full email structure)
        html_body = format_html_email_with_ai_content(issue_data, ai_html)
    else:
        # Fallback to old format if no HTML from AI
        # Try to extract WWWH-TR sections from raw content
        raw_content = analysis.get("raw", "")
        fallback_analysis = _extract_wwwh_tr_fallback(raw_content)
        html_body = format_html_email(issue_data, fallback_analysis)

    # Generate plain text version from raw content
    raw_content = analysis.get("raw", "")
    text_body = format_text_email_from_raw(issue_data, raw_content)

    return {"subject": subject, "html": html_body, "text": text_body}


def format_html_email(issue_data: Dict[str, Any], analysis: Dict[str, str]) -> str:
    """
    Format issue data and analysis as HTML email.

    Args:
        issue_data: Issue data dictionary
        analysis: WWWH-TR analysis dictionary

    Returns:
        HTML email body string
    """
    # Extract issue information
    title = issue_data.get("title", "Untitled Issue")
    url = issue_data.get("web_url") or issue_data.get("url", "#")
    state = issue_data.get("state", "unknown")

    # Format labels with color mapping
    labels = issue_data.get("labels", [])
    labels_html = ""
    if labels:
        labels_list = []
        for label in labels:
            label_name = (
                label.get("name", label) if isinstance(label, dict) else str(label)
            )
            label_color = get_label_color(str(label_name))
            text_color = get_text_color_for_background(label_color)
            label_escaped = html.escape(str(label_name))
            labels_list.append(
                f'<span style="background-color: {label_color}; color: {text_color}; padding: 2px 6px; border-radius: 16px; margin-right: 4px;">{label_escaped}</span>'
            )
        labels_html = "".join(labels_list)

    # Format assignee
    assignee = issue_data.get("assignee")
    if isinstance(assignee, dict):
        assignee_str = assignee.get("username", assignee.get("name", "Unassigned"))
    elif assignee:
        assignee_str = str(assignee)
    else:
        assignee_str = "Unassigned"

    # Format author
    author = issue_data.get("author")
    if isinstance(author, dict):
        author_str = author.get("username", author.get("name", "Unknown"))
    elif author:
        author_str = str(author)
    else:
        author_str = "Unknown"

    # Format WWWH-TR sections
    w1_html = _format_section_html("W1 — Why", analysis.get("W1", ""))
    w2_html = _format_section_html("W2 — What", analysis.get("W2", ""))
    w3_html = _format_section_html("W3 — Who", analysis.get("W3", ""))
    h_html = _format_section_html("H — How", analysis.get("H", ""))
    t_html = _format_section_html("T — Test", analysis.get("T", ""))
    r_html = _format_section_html("R — Reflect", analysis.get("R", ""))

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .section {{
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 4px solid #4CAF50;
            border-radius: 3px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .section-content {{
            color: #555;
            white-space: pre-wrap;
        }}
        .issue-link {{
            color: #0066cc;
            text-decoration: none;
        }}
        .issue-link:hover {{
            text-decoration: underline;
        }}
        .metadata {{
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin-top: 0;">{title}</h1>
        <p><strong>URL:</strong> <a href="{url}" class="issue-link">{url}</a></p>
        <p><strong>State:</strong> {state} | <strong>Assignee:</strong> {assignee_str} | <strong>Author:</strong> {author_str}</p>
        {f'<p><strong>Labels:</strong> {labels_html}</p>' if labels_html else ''}
    </div>

    {w1_html}
    {w2_html}
    {w3_html}
    {h_html}
    {t_html}
    {r_html}

    <div class="metadata">
        <p><em>Generated by GitLab Issues Analyzer</em></p>
        <p><em>Issue URL: <a href="{url}" class="issue-link">{url}</a></em></p>
    </div>
</body>
</html>"""

    return html


def format_text_email(issue_data: Dict[str, Any], analysis: Dict[str, str]) -> str:
    """
    Format issue data and analysis as plain text email.

    Args:
        issue_data: Issue data dictionary
        analysis: WWWH-TR analysis dictionary

    Returns:
        Plain text email body string
    """
    # Extract issue information
    title = issue_data.get("title", "Untitled Issue")
    url = issue_data.get("web_url") or issue_data.get("url", "#")
    state = issue_data.get("state", "unknown")

    # Format labels
    labels = issue_data.get("labels", [])
    labels_str = "None"
    if labels:
        labels_list = [
            label.get("name", label) if isinstance(label, dict) else str(label)
            for label in labels
        ]
        labels_str = ", ".join(labels_list)

    # Format assignee
    assignee = issue_data.get("assignee")
    if isinstance(assignee, dict):
        assignee_str = assignee.get("username", assignee.get("name", "Unassigned"))
    elif assignee:
        assignee_str = str(assignee)
    else:
        assignee_str = "Unassigned"

    # Format author
    author = issue_data.get("author")
    if isinstance(author, dict):
        author_str = author.get("username", author.get("name", "Unknown"))
    elif author:
        author_str = str(author)
    else:
        author_str = "Unknown"

    # Format WWWH-TR sections
    w1_text = _format_section_text("W1 — Why", analysis.get("W1", ""))
    w2_text = _format_section_text("W2 — What", analysis.get("W2", ""))
    w3_text = _format_section_text("W3 — Who", analysis.get("W3", ""))
    h_text = _format_section_text("H — How", analysis.get("H", ""))
    t_text = _format_section_text("T — Test", analysis.get("T", ""))
    r_text = _format_section_text("R — Reflect", analysis.get("R", ""))

    text = f"""GitLab Issue Analysis
{'=' * 60}

Title: {title}
URL: {url}
State: {state}
Assignee: {assignee_str}
Author: {author_str}
Labels: {labels_str}

{'=' * 60}

{w1_text}

{w2_text}

{w3_text}

{h_text}

{t_text}

{r_text}

{'=' * 60}

Generated by GitLab Issues Analyzer
Issue URL: {url}
"""

    return text


def _format_section_html(title: str, content: str) -> str:
    """
    Format a WWWH-TR section as HTML.

    Args:
        title: Section title
        content: Section content

    Returns:
        HTML string for the section
    """
    if not content:
        return ""

    return f"""<div class="section">
    <div class="section-title">{title}</div>
    <div class="section-content">{content}</div>
</div>"""


def _format_section_text(title: str, content: str) -> str:
    """
    Format a WWWH-TR section as plain text.

    Args:
        title: Section title
        content: Section content

    Returns:
        Plain text string for the section
    """
    if not content:
        return ""

    return f"""{title}
{'-' * len(title)}
{content}
"""


def format_html_email_with_ai_content(issue_data: Dict[str, Any], ai_html: str) -> str:
    """
    Format email with AI-generated HTML content.

    Args:
        issue_data: Issue data dictionary
        ai_html: AI-generated HTML content (should already include header card with title/URL)

    Returns:
        Complete HTML email body
    """
    # Extract issue URL for footer link only
    url = issue_data.get("web_url") or issue_data.get("url", "#")

    # Wrap AI HTML in a complete email structure
    # The AI HTML should already include the header card with title, state, priority, and URL
    # So we don't duplicate it here - just wrap the AI content in a clean email structure
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f5f5f5;">
        <tr>
            <td style="padding: 20px;">
                <table role="presentation" style="width: 100%; max-width: 800px; margin: 0 auto; background-color: #ffffff; border-collapse: collapse; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 20px;">
                            {ai_html}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #999; text-align: center;">
                            <p style="margin: 0;">Generated by GitLab Issues Analyzer</p>
                            <p style="margin: 5px 0 0 0;">
                                <a href="{url}" style="color: #0066cc; text-decoration: none;">View Issue</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    return html


def format_text_email_from_raw(issue_data: Dict[str, Any], raw_content: str) -> str:
    """
    Format plain text email from raw AI content.

    Args:
        issue_data: Issue data dictionary
        raw_content: Raw AI response content

    Returns:
        Plain text email body
    """
    import re

    title = issue_data.get("title", "Untitled Issue")
    url = issue_data.get("web_url") or issue_data.get("url", "#")

    # Remove HTML tags for plain text version
    text_content = re.sub(r"<[^>]+>", "", raw_content)
    text_content = text_content.replace("&nbsp;", " ")
    text_content = text_content.replace("&amp;", "&")
    text_content = text_content.replace("&lt;", "<")
    text_content = text_content.replace("&gt;", ">")

    text = f"""GitLab Issue Analysis
{'=' * 60}

Title: {title}
URL: {url}

{'=' * 60}

{text_content}

{'=' * 60}

Generated by GitLab Issues Analyzer
Issue URL: {url}
"""

    return text


def _extract_wwwh_tr_fallback(content: str) -> Dict[str, str]:
    """
    Fallback: Extract WWWH-TR sections from raw content if AI didn't provide HTML.

    Args:
        content: Raw content from AI

    Returns:
        Dictionary with W1, W2, W3, H, T, R sections
    """
    import re

    sections = {"W1": "", "W2": "", "W3": "", "H": "", "T": "", "R": ""}

    # Simple pattern matching for fallback
    patterns = {
        "W1": [
            r"(?i)W1[:\s—\-]*Why[:\s]*(.*?)(?=W2|H|T|R|$)",
            r"(?i)Why[:\s]*(.*?)(?=What|Who|How|Test|Reflect|$)",
        ],
        "W2": [
            r"(?i)W2[:\s—\-]*What[:\s]*(.*?)(?=W3|H|T|R|$)",
            r"(?i)What[:\s]*(.*?)(?=Who|How|Test|Reflect|$)",
        ],
        "W3": [
            r"(?i)W3[:\s—\-]*Who[:\s]*(.*?)(?=H|T|R|$)",
            r"(?i)Who[:\s]*(.*?)(?=How|Test|Reflect|$)",
        ],
        "H": [
            r"(?i)H[:\s—\-]*How[:\s]*(.*?)(?=T|R|$)",
            r"(?i)How[:\s]*(.*?)(?=Test|Reflect|$)",
        ],
        "T": [
            r"(?i)T[:\s—\-]*Test[:\s]*(.*?)(?=R|$)",
            r"(?i)Test[:\s]*(.*?)(?=Reflect|$)",
        ],
        "R": [r"(?i)R[:\s—\-]*Reflect[:\s]*(.*?)$", r"(?i)Reflect[:\s]*(.*?)$"],
    }

    for section, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                sections[section] = match.group(1).strip()
                break

    # If no sections found, use content as W1
    if not any(sections.values()):
        sections["W1"] = content[:1000] if len(content) > 1000 else content

    return sections
