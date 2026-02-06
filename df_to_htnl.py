import pandas as pd

# 1. Setup sample data
data = {
    'Underlying': ['S&P 500', 'Nasdaq 100', 'FTSE 100', 'DAX', 'Nikkei 225', 'CAC 40'],
    'Diff': [12.5, -5.2, 3.1, -1.8, 15.4, 0.5],
    '10MA': [4520.1, 15100.5, 7500.2, 15800.0, 32000.8, 7200.3],
    'Threshold': [10.0, 10.0, 5.0, 5.0, 12.0, 5.0]
}

df = pd.DataFrame(data)

def generate_email_html(df):
    # Apply styling
    styled_df = df.style.set_table_attributes('cellspacing="0" cellpadding="8" style="border-collapse: collapse; font-family: sans-serif; min-width: 400px; border: 1px solid #dddddd;"')
    
    # Header styling
    styled_df.set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#1f2937'), ('color', 'white'), ('text-align', 'left'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('border-bottom', '1px solid #eeeeee')]}
    ])

    # Conditional Formatting: Highlight 'Diff' if it exceeds 'Threshold'
    def highlight_threshold(row):
        color = '#fecaca' if abs(row['Diff']) > row['Threshold'] else 'transparent'
        return [f'background-color: {color}' for _ in row]

    # Apply row-level styling and format numbers
    styled_df = styled_df.apply(highlight_threshold, axis=1)
    styled_df = styled_df.format({'Diff': '{:+.2f}', '10MA': '{:,.2f}', 'Threshold': '{:.1f}'})
    
    # Hide the index for a cleaner look
    html_output = styled_df.hide(axis='index').to_html()
    
    return html_output

# Generate and save/print
html_table = generate_email_html(df)

# Wrap in a basic container for the email body
full_email_body = f"""
<html>
<body style="margin: 20px;">
    <h2 style="color: #333;">Market Summary Report</h2>
    <p>The table below summarizes the current performance against 10-day moving averages.</p>
    {html_table}
    <p style="font-size: 12px; color: #666; margin-top: 20px;">
        * Rows highlighted in red indicate the difference has exceeded the set threshold.
    </p>
</body>
</html>
"""

print(full_email_body)
