"""Constellation catalog shared by Settings and the radial ring painter.

Coordinates are normalized to a 0..1 drawing rectangle.  They are deliberately
stylized for a compact launcher rather than intended as an astronomical chart.
"""
from __future__ import annotations

from typing import TypedDict


class ConstellationData(TypedDict):
    name: str
    name_zh: str
    symbol: str
    stars: tuple[tuple[float, float, float], ...]
    links: tuple[tuple[int, int], ...]


DEFAULT_CONSTELLATION = "scorpio"
DEFAULT_CONSTELLATION_COLOR = "#F2760B"

CONSTELLATION_ORDER = (
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
)

CONSTELLATIONS: dict[str, ConstellationData] = {
    "aries": {
        "name": "Aries", "name_zh": "牡羊座", "symbol": "♈",
        "stars": ((.18,.58,1.0),(.34,.43,.7),(.50,.38,.9),(.64,.45,.65),(.79,.34,.8)),
        "links": ((0,1),(1,2),(2,3),(3,4)),
    },
    "taurus": {
        "name": "Taurus", "name_zh": "金牛座", "symbol": "♉",
        "stars": ((.12,.22,.65),(.36,.43,.85),(.50,.58,1.0),(.64,.43,.85),(.88,.20,.7),(.50,.80,.65)),
        "links": ((0,1),(1,2),(2,3),(3,4),(2,5)),
    },
    "gemini": {
        "name": "Gemini", "name_zh": "雙子座", "symbol": "♊",
        "stars": ((.28,.18,.85),(.34,.42,.65),(.31,.72,1.0),(.70,.16,.9),(.65,.43,.7),(.72,.78,.85)),
        "links": ((0,1),(1,2),(3,4),(4,5),(0,3),(2,5)),
    },
    "cancer": {
        "name": "Cancer", "name_zh": "巨蟹座", "symbol": "♋",
        "stars": ((.19,.28,.7),(.39,.44,.85),(.53,.55,1.0),(.71,.40,.7),(.78,.20,.55),(.58,.78,.7)),
        "links": ((0,1),(1,2),(2,3),(3,4),(2,5)),
    },
    "leo": {
        "name": "Leo", "name_zh": "獅子座", "symbol": "♌",
        "stars": ((.15,.62,.65),(.34,.55,.8),(.53,.58,1.0),(.68,.43,.75),(.63,.24,.65),(.78,.18,.8),(.86,.34,.6)),
        "links": ((0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,3)),
    },
    "virgo": {
        "name": "Virgo", "name_zh": "處女座", "symbol": "♍",
        "stars": ((.14,.30,.55),(.33,.42,.7),(.50,.48,1.0),(.66,.31,.7),(.84,.24,.55),(.65,.66,.85),(.79,.80,.65),(.39,.75,.6)),
        "links": ((0,1),(1,2),(2,3),(3,4),(2,5),(5,6),(5,7)),
    },
    "libra": {
        "name": "Libra", "name_zh": "天秤座", "symbol": "♎",
        "stars": ((.16,.28,.65),(.36,.42,.8),(.50,.67,1.0),(.67,.42,.85),(.85,.26,.65),(.28,.76,.55),(.74,.77,.6)),
        "links": ((0,1),(1,2),(2,3),(3,4),(1,3),(2,5),(2,6)),
    },
    "scorpio": {
        "name": "Scorpio", "name_zh": "天蠍座", "symbol": "♏",
        "stars": ((.12,.24,.6),(.24,.36,.7),(.38,.43,.8),(.52,.50,1.0),(.65,.60,.8),(.72,.76,.7),(.84,.72,.8),(.89,.57,.65),(.81,.47,.55)),
        "links": ((0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8)),
    },
    "sagittarius": {
        "name": "Sagittarius", "name_zh": "射手座", "symbol": "♐",
        "stars": ((.16,.72,.6),(.35,.57,.75),(.52,.61,.9),(.67,.45,1.0),(.84,.24,.8),(.52,.33,.7),(.30,.29,.65),(.70,.75,.55)),
        "links": ((0,1),(1,2),(2,3),(3,4),(3,5),(5,6),(1,6),(2,7)),
    },
    "capricorn": {
        "name": "Capricorn", "name_zh": "摩羯座", "symbol": "♑",
        "stars": ((.13,.34,.65),(.31,.26,.8),(.49,.39,1.0),(.66,.31,.75),(.84,.43,.7),(.71,.67,.8),(.48,.76,.65),(.27,.64,.6)),
        "links": ((0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,0),(2,6)),
    },
    "aquarius": {
        "name": "Aquarius", "name_zh": "水瓶座", "symbol": "♒",
        "stars": ((.10,.33,.6),(.27,.25,.75),(.43,.37,.65),(.60,.27,1.0),(.78,.38,.7),(.92,.28,.6),(.20,.64,.55),(.39,.55,.7),(.58,.67,.65),(.79,.57,.6)),
        "links": ((0,1),(1,2),(2,3),(3,4),(4,5),(6,7),(7,8),(8,9)),
    },
    "pisces": {
        "name": "Pisces", "name_zh": "雙魚座", "symbol": "♓",
        "stars": ((.12,.22,.65),(.25,.34,.75),(.20,.51,.6),(.34,.58,.8),(.50,.52,1.0),(.65,.44,.75),(.80,.52,.65),(.88,.68,.8),(.73,.79,.6)),
        "links": ((0,1),(1,2),(2,3),(3,4),(4,5),(5,6),(6,7),(7,8),(8,5)),
    },
}


def constellation_label(constellation_id: str) -> str:
    data = CONSTELLATIONS.get(constellation_id, CONSTELLATIONS[DEFAULT_CONSTELLATION])
    return f"{data['symbol']}  {data['name_zh']} / {data['name']}"


def normalise_constellation_color(value: object) -> str:
    text = str(value or "").strip()
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
        except ValueError:
            pass
        else:
            return text.upper()
    return DEFAULT_CONSTELLATION_COLOR
