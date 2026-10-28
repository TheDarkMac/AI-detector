"""Taux mesurés et leur intervalle de confiance (A-54, ADR-0101, ADR-0104).

Chaque taux est publié avec son effectif et l'intervalle de Wilson à 95 %. L'intervalle de
Wilson reste dans [0, 1] et garde un sens pour un taux nul, contrairement à l'approximation
normale ; c'est sa borne supérieure qui fixe le niveau permis d'une règle (ADR-0101).
"""

import math
from dataclasses import dataclass

__all__ = ["CONFIANCE", "Taux"]

CONFIANCE = 0.95
Z = 1.959963984540054
"""Quantile de la loi normale pour une confiance bilatérale de 95 %."""


@dataclass(frozen=True, slots=True)
class Taux:
    """``nombre`` cas sur ``effectif`` fichiers ; sans effectif, aucun taux n'est mesuré."""

    nombre: int
    effectif: int

    def __post_init__(self) -> None:
        if not 0 <= self.nombre <= self.effectif:
            raise ValueError("taux : 0 ≤ nombre ≤ effectif attendu")

    @property
    def mesure(self) -> bool:
        return self.effectif > 0

    @property
    def valeur(self) -> float | None:
        return self.nombre / self.effectif if self.effectif else None

    @property
    def intervalle(self) -> tuple[float, float] | None:
        """Intervalle de Wilson à 95 %."""
        if not self.effectif:
            return None
        n, p = self.effectif, self.nombre / self.effectif
        z2 = Z * Z
        denominateur = 1 + z2 / n
        centre = (p + z2 / (2 * n)) / denominateur
        demi = Z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n)) / denominateur
        # Aux extrémités, la borne vaut exactement 0 ou 1 ; le calcul en flottants s'en écarte.
        basse = 0.0 if self.nombre == 0 else max(0.0, centre - demi)
        haute = 1.0 if self.nombre == n else min(1.0, centre + demi)
        return basse, haute

    @property
    def borne_superieure(self) -> float | None:
        intervalle = self.intervalle
        return None if intervalle is None else intervalle[1]

    def vers_dict(self) -> dict[str, object]:
        intervalle = self.intervalle
        return {
            "nombre": self.nombre,
            "effectif": self.effectif,
            "valeur": self.valeur,
            "intervalle": None if intervalle is None else list(intervalle),
        }
