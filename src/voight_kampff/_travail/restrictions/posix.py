"""Limites de ressources communes à Linux et macOS (``setrlimit``)."""

__all__ = ["limiter"]


def limiter(ressource: int, valeur: int, marge: int = 0) -> bool:  # pragma: no cover - travail
    """Pose la limite ``valeur`` (dure : ``valeur + marge``) ; une limite plus stricte est gardée.

    Exécuté seulement dans un processus de travail : ``resource`` est importé ici, ce module
    étant importé aussi sous Windows par les tests.
    """
    import resource

    try:
        _douce, dure = resource.getrlimit(ressource)
        if dure != resource.RLIM_INFINITY and dure <= valeur + marge:
            resource.setrlimit(ressource, (min(valeur, dure), dure))
        else:
            resource.setrlimit(ressource, (valeur, valeur + marge))
    except (OSError, ValueError):
        return False
    return True
