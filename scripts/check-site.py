#!/usr/bin/env python3
"""Validate a built bilingual site, offline. Run after a clean Hugo build."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

CORE = {
    'docs/about/': (),
    'docs/features/': (),
    'docs/get-started/': (),
    'docs/get-started/reading-results/': ('6803c61', '436492'),
    'docs/scenarios/slow-sql/': ('6803c61', '436010'),
    'docs/scenarios/lock-waits/': ('6803c61', '435308'),
    'docs/reference/': (),
    'docs/reference/sessions/': ('84c883e', '320047'),
    'docs/reference/session/': ('0a4d61e', '367208'),
    'docs/reference/locks/': ('0a4d61e', '364809'),
    'docs/reference/txn/': ('0a4d61e', 'kbdiag_inj_2pc'),
    'docs/reference/waits/': ('0a4d61e', '364818'),
    'docs/reference/status/': ('6803c61', 'inst.connections'),
    'docs/reference/slots/': ('6803c61', 'walreceiver'),
}

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.indexes, self.text = set(), [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag in ('a', 'link') and 'href' in attrs:
            self.links.append(attrs['href'])
        if tag in ('script', 'img') and 'src' in attrs:
            self.links.append(attrs['src'])
        if attrs.get('data-td-index-src'):
            self.indexes.append(attrs['data-td-index-src'])
            self.links.append(attrs['data-td-index-src'])

    def handle_data(self, text):
        self.text.append(text)


def validate(root, base, required=None):
    root = root.resolve()
    base = base.rstrip('/') + '/'
    origin = urlsplit(base)
    pages = {p: Page(p.read_text()) for p in root.rglob('*.html')}
    errors, checks = [], 0
    if not pages:
        errors.append('No HTML files: run Hugo first')

    def local_target(source, link):
        target = urlsplit(urljoin(source, link))
        if target.scheme not in ('http', 'https') or target.netloc.lower() != origin.netloc.lower():
            return None, None
        if not target.path.startswith(origin.path):
            errors.append(f'{link}: outside baseURL {origin.path}')
            return None, None
        path = (root / unquote(target.path[len(origin.path):])).resolve()
        if not path.is_relative_to(root):
            errors.append(f'{link}: escapes output directory')
            return None, None
        if path.is_dir():
            path /= 'index.html'
        return path, unquote(target.fragment)

    indexes = set()
    for path, page in pages.items():
        rel = path.relative_to(root).as_posix()
        source = base + (rel[:-10] if rel.endswith('index.html') else rel)
        for link in page.links:
            target, anchor = local_target(source, link)
            if target is None:
                continue
            checks += 1
            if not target.is_file():
                errors.append(f'{rel}: missing target {link}')
            elif anchor and target in pages and anchor not in pages[target].ids:
                errors.append(f'{rel}: missing anchor {link}')
        for link in page.indexes:
            target, _ = local_target(source, link)
            if target:
                indexes.add(target)

    required = CORE if required is None else required
    for prefix in ('', 'zh/'):
        for route, tokens in required.items():
            path = root / prefix / route / 'index.html'
            if path not in pages:
                errors.append(f'Missing required page: {prefix}{route}')
                continue
            text = ''.join(pages[path].text)
            for token in tokens:
                if token not in text:
                    errors.append(f'{prefix}{route}: missing evidence marker {token!r}')
    if required and not indexes:
        errors.append('No search indexes referenced by rendered HTML')
    for index in indexes:
        try:
            data = json.loads(index.read_text())
        except (OSError, ValueError) as exc:
            errors.append(f'Invalid search index {index.name}: {exc}')
            continue
        # OINK indexes are arrays of records with a ref URL.
        records = data if isinstance(data, list) else data.values() if isinstance(data, dict) else []
        for record in records:
            if not isinstance(record, dict):
                continue
            link = record.get('ref') or record.get('uri') or record.get('permalink')
            if link:
                path, _ = local_target(base, link)
                if path is not None and not path.is_file():
                    errors.append(f'Search index {index.name}: missing {link}')
    return errors, len(pages), checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('public'))
    parser.add_argument('--base-url', default='https://kevin-wenyu.github.io/kbdiag-docs/')
    args = parser.parse_args()
    errors, pages, checks = validate(args.root, args.base_url)
    for error in errors:
        print(error)
    print(f'{pages} HTML pages; {checks} link checks; {len(errors)} failures')
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
