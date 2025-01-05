import textwrap

def wrap_text(text, width):
    """Wrap text to specified width"""
    return '\n'.join(textwrap.wrap(text, width=width))

def clean_text(text):
    """Clean text by replacing escaped quotes and other potential issues"""
    return text.replace('\\"', '"') 