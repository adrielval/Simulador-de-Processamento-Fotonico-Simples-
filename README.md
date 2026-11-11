# Simulador-de-Processamento-Fotonico-Simples-
==========================

Objetivo:
- Simular 2 entradas ópticas (laser A e laser B).
- Cada entrada carrega 1 byte (8 bits).
- Cada bit '1' liga o laser naquele intervalo de tempo.
- Os dois sinais percorrem guias de onda com atraso e perda.
- Os sinais são combinados e detectados por um fotodetector.
- O programa estima:
    * atraso óptico em cada braço,
    * diferença de atraso,
    * potência óptica resultante bit a bit,
    * corrente do fotodetector,
    * tempo estimado por bit,
    * tempo estimado por byte.

IMPORTANTE:
Este é um modelo de estudo, não um simulador de fabricação.
Ele NÃO substitui FDTD/EME/BPM ou ferramentas como Lumerical/COMSOL/Meep.
==========================
