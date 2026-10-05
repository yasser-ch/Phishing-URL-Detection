import re


def url_tokenizer(url):
    """Découpe une URL en mots (lettres uniquement) pour la vectorisation
    TF-IDF. Doit rester dans un module importable (pas défini directement
    dans un notebook) pour que joblib puisse recharger le modèle
    correctement ailleurs — autre notebook, Flask, etc."""
    return re.findall(r'[a-zA-Z]+', url.lower())