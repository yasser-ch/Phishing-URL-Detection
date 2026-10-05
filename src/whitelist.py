import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHITELIST_FILE = os.path.join(BASE_DIR, 'data', 'whitelist_domains.txt')

TRUSTED_TLDS = {
    '.gov.ma',
    '.gov',
    '.edu',
    '.ac.ma',
}

_trusted_domains = None


def load_trusted_domains():
    global _trusted_domains
    if _trusted_domains is not None:
        return _trusted_domains

    domains = set()
    try:
        with open(WHITELIST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip().lower()
                if line and not line.startswith('#'):
                    domains.add(line)
    except FileNotFoundError:
        domains = set()

    _trusted_domains = domains
    return domains


def is_whitelisted(domain):
    domain = domain.lower().strip()
    trusted_domains = load_trusted_domains()

    if domain.startswith('www.'):
        bare = domain[4:]
    else:
        bare = domain

    if domain in trusted_domains or bare in trusted_domains:
        return True, 'domaine de confiance'

    for trusted in trusted_domains:
        if bare.endswith('.' + trusted):
            return True, f'sous-domaine de {trusted}'

    for tld in TRUSTED_TLDS:
        if bare.endswith(tld):
            return True, f'TLD institutionnel ({tld})'

    return False, None