"""
Helper functions untuk IoT Hydroponics Dashboard
"""

def safe_float(x, default=0.0):
    """Safely convert value to float"""
    try:
        return float(x)
    except:
        return default

def get_label_color(label):
    """Get color for a label"""
    from config import LABEL_COLORS
    return LABEL_COLORS.get(label, 'gray')