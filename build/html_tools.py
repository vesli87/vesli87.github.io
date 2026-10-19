"""Small HTML readers; document data is parsed, never executed or regex-extracted."""
import json
from html.parser import HTMLParser


class StructuredData(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.blocks = []
        self.current = None
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') == 'application/ld+json':
            self.current = []

    def handle_data(self, text):
        if self.current is not None:
            self.current.append(text)

    def handle_endtag(self, tag):
        if tag == 'script' and self.current is not None:
            self.blocks.append(json.loads(''.join(self.current)))
            self.current = None


def structured_data(text):
    return StructuredData(text).blocks


def rewrite_start_tags(text, transform):
    """Rewrite actual opening tags, preserving every other input byte/character.

    HTMLParser handles quoted >, comments and script/style raw text. This is a
    content-fingerprint helper, not an HTML sanitizer.
    """
    lines = [0]
    for index, char in enumerate(text):
        if char == '\n':
            lines.append(index + 1)
    replacements = []

    class Tags(HTMLParser):
        def handle_starttag(self, tag, attrs):
            raw = self.get_starttag_text()
            row, column = self.getpos()
            start = lines[row - 1] + column
            replacements.append((start, start + len(raw), transform(raw)))

        handle_startendtag = handle_starttag

    parser = Tags(convert_charrefs=False)
    parser.feed(text)
    parser.close()
    parts, start = [], 0
    for first, end, replacement in replacements:
        parts.extend((text[start:first], replacement))
        start = end
    parts.append(text[start:])
    return ''.join(parts)
