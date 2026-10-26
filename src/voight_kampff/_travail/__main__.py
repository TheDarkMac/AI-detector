"""Point d'entrée du processus de travail : ``python -I -B -m voight_kampff._travail``."""

import sys

from voight_kampff._travail.principal import canal_du_protocole, principal

sys.exit(principal(sys.argv[1:], sys.stdin.buffer, canal_du_protocole()))
