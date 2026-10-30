"""Presets de tipos de tornado para crear instancias `Tornado` rapidamente.

Cada preset es un diccionario de kwargs valido para ``Tornado(**preset)``.
Se pueden sobreescribir parametros puntuales::

    from templates import tornado, tornado_presets
    big = tornado.Tornado(name="Tornado_F01",
                          **tornado_presets.with_overrides("f5", height=25))
"""

TORNADO_TYPES = {
    # Cordón fino y alto, muy rotativo (tornado clasico de las llanuras)
    "rope": {
        "height": 10.0,
        "bottom_radius": 0.6,
        "top_radius": 1.8,
        "particle_count": 4000,
        "particle_lifetime": 90,
        "emission_start": 1,
        "emission_end": 70,
        "rotation_speed": 2.4,
        "upward_speed": 0.45,
        "seed": 11,
    },
    # Columna ancha tipo cono/stadium cone (tornado fuerte, estable)
    "cone": {
        "height": 8.0,
        "bottom_radius": 2.2,
        "top_radius": 2.6,
        "particle_count": 8000,
        "particle_lifetime": 110,
        "emission_start": 1,
        "emission_end": 90,
        "rotation_speed": 1.0,
        "upward_speed": 0.3,
        "seed": 23,
    },
    # Embudo ancho abajo y afinado arriba (silueta clasica de embudo)
    "funnel": {
        "height": 9.0,
        "bottom_radius": 2.0,
        "top_radius": 0.4,
        "particle_count": 7000,
        "particle_lifetime": 100,
        "emission_start": 1,
        "emission_end": 80,
        "rotation_speed": 1.6,
        "upward_speed": 0.4,
        "seed": 37,
    },
    # F5 cinematografico: enorme, denso y violento
    "f5": {
        "height": 18.0,
        "bottom_radius": 4.0,
        "top_radius": 1.2,
        "particle_count": 15000,
        "particle_lifetime": 140,
        "emission_start": 1,
        "emission_end": 120,
        "rotation_speed": 3.2,
        "upward_speed": 0.6,
        "seed": 99,
    },
    # Mini-tornado/dust devil: pequeño, ligero, translucido
    "dust_devil": {
        "height": 4.0,
        "bottom_radius": 0.8,
        "top_radius": 0.3,
        "particle_count": 2500,
        "particle_lifetime": 60,
        "emission_start": 1,
        "emission_end": 45,
        "rotation_speed": 1.8,
        "upward_speed": 0.25,
        "seed": 5,
    },
}


def get(tipo: str) -> dict:
    """Devuelve una COPIA del preset ``tipo`` (mutable por el caller)."""
    try:
        return dict(TORNADO_TYPES[tipo])
    except KeyError:
        validos = ", ".join(sorted(TORNADO_TYPES))
        raise KeyError(f"Tipo de tornado desconocido: {tipo!r}. Validos: {validos}") from None


def with_overrides(tipo: str, **overrides) -> dict:
    """Preset ``tipo`` con parametros puntuales sobrescritos.

    La validacion fina de cada parametro la hace la clase ``Tornado``;
    aqui solo se compone el diccionario.
    """
    cfg = get(tipo)
    cfg.update(overrides)
    return cfg


def register_type(nombre: str, config: dict):
    """Registra un tipo nuevo de tornado (extension sin tocar el modulo)."""
    if not nombre.strip():
        raise ValueError("El nombre del tipo no puede estar vacio")
    if not isinstance(config, dict):
        raise TypeError("El preset debe ser un diccionario de kwargs")
    TORNADO_TYPES[nombre] = dict(config)
