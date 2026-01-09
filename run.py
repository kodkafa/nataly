from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

from nataly import NatalChart, create_orb_config, to_utc


TOutputFormat = Literal["text", "json", "both"]


@dataclass(frozen=True)
class PluginInput:
    person: str
    birth: str
    tz: str
    lat: float
    lon: float
    house_system: str
    ephe_path: Optional[str]
    output_format: TOutputFormat


@dataclass(frozen=True)
class AspectOut:
    body1: str
    symbol: str
    body2: str
    orb: str


@dataclass(frozen=True)
class BodyOut:
    name: str
    signed_dms: str
    house: Optional[int]
    declination_dms: Optional[str]
    absolute_dms: Optional[str]


@dataclass(frozen=True)
class HouseOut:
    id: int
    dms: str
    sign: str
    declination_dms: Optional[str]
    absolute_dms: Optional[str]


@dataclass(frozen=True)
class ChartSummaryOut:
    person: str
    dt_utc_iso: str
    location: Dict[str, float]
    sun: Optional[BodyOut]
    moon: Optional[BodyOut]
    aspects: List[AspectOut]
    element_distribution: Any
    modality_distribution: Any
    houses: List[HouseOut]


_TZ_RE = re.compile(r"^[+-](?:0\d|1\d|2[0-3]):[0-5]\d$")


def _parse_args(argv: List[str]) -> PluginInput:
    parser = argparse.ArgumentParser(prog="nataly (KODKAFA plugin)")
    parser.add_argument("--person", required=True)
    parser.add_argument("--birth", required=True, help="YYYY-MM-DD HH:MM")
    parser.add_argument("--tz", required=True, help="UTC offset (e.g. +02:00)")
    parser.add_argument("--lat", required=True, type=float)
    parser.add_argument("--lon", required=True, type=float)
    parser.add_argument("--house-system", default="Placidus")
    parser.add_argument("--ephe-path", default=None)
    parser.add_argument("--format", choices=["text", "json", "both"], default="text")

    ns = parser.parse_args(argv)

    tz = str(ns.tz).strip()
    if not _TZ_RE.match(tz):
        raise ValueError(f"Invalid --tz value: {tz}. Expected format like +02:00")

    return PluginInput(
        person=str(ns.person).strip(),
        birth=str(ns.birth).strip(),
        tz=tz,
        lat=float(ns.lat),
        lon=float(ns.lon),
        house_system=str(ns.house_system).strip(),
        ephe_path=(str(ns.ephe_path).strip() if ns.ephe_path else None),
        output_format=str(ns.format),  # type: ignore[return-value]
    )


def _resolve_ephe_path(explicit: Optional[str]) -> Optional[str]:
    if explicit:
        return explicit

    env_val = os.getenv("NATALY_EPHE_PATH")
    if env_val and env_val.strip():
        return env_val.strip()

    plugin_dir = Path(__file__).resolve().parent
    default_dir = plugin_dir / "ephe"
    if default_dir.exists() and default_dir.is_dir():
        return str(default_dir)

    return None


def _safe_get_body(chart: NatalChart, name: str) -> Optional[BodyOut]:
    try:
        body = chart.get_body_by_name(name)
    except Exception:
        return None

    house_val: Optional[int]
    try:
        house_val = int(getattr(body, "house"))
    except Exception:
        house_val = None

    signed_dms = str(getattr(body, "signed_dms", "")) or str(getattr(body, "dms", ""))
    decl_dms = getattr(body, "declination_dms", None)
    abs_dms = getattr(body, "absolute_dms", None)

    return BodyOut(
        name=str(getattr(body, "name", name)),
        signed_dms=str(signed_dms),
        house=house_val,
        declination_dms=(str(decl_dms) if decl_dms is not None else None),
        absolute_dms=(str(abs_dms) if abs_dms is not None else None),
    )


def _build_chart(inp: PluginInput) -> Tuple[NatalChart, str]:
    dt_utc = to_utc(inp.birth, inp.tz)
    dt_utc_iso = dt_utc.isoformat()

    ephe_path = _resolve_ephe_path(inp.ephe_path)
    orb_cfg = create_orb_config(inp.house_system)

    chart = NatalChart(
        person_name=inp.person,
        dt_utc=dt_utc,
        lat=inp.lat,
        lon=inp.lon,
        orb_config=orb_cfg,
        ephe_path=ephe_path,
    )
    return chart, dt_utc_iso


def _to_summary(chart: NatalChart, inp: PluginInput, dt_utc_iso: str) -> ChartSummaryOut:
    sun = _safe_get_body(chart, "Sun")
    moon = _safe_get_body(chart, "Moon")

    aspects_out: List[AspectOut] = []
    for asp in getattr(chart, "aspects", []):
        b1 = getattr(getattr(asp, "body1", None), "name", "")
        b2 = getattr(getattr(asp, "body2", None), "name", "")
        sym = getattr(asp, "symbol", "")
        orb = getattr(asp, "orb_str", "")
        aspects_out.append(AspectOut(body1=str(b1), symbol=str(sym), body2=str(b2), orb=str(orb)))

    houses_out: List[HouseOut] = []
    for h in getattr(chart, "houses", []):
        hid = int(getattr(h, "id"))
        dms = str(getattr(h, "dms", ""))
        sign = str(getattr(getattr(h, "sign", None), "name", ""))
        decl = getattr(h, "declination_dms", None)
        abs_dms = getattr(h, "absolute_dms", None)
        houses_out.append(
            HouseOut(
                id=hid,
                dms=dms,
                sign=sign,
                declination_dms=(str(decl) if decl is not None else None),
                absolute_dms=(str(abs_dms) if abs_dms is not None else None),
            )
        )

    return ChartSummaryOut(
        person=inp.person,
        dt_utc_iso=dt_utc_iso,
        location={"lat": inp.lat, "lon": inp.lon},
        sun=sun,
        moon=moon,
        aspects=aspects_out,
        element_distribution=getattr(chart, "element_distribution", None),
        modality_distribution=getattr(chart, "modality_distribution", None),
        houses=houses_out,
    )


def _print_text(summary: ChartSummaryOut) -> None:
    print(f"Person: {summary.person}")
    print(f"UTC:    {summary.dt_utc_iso}")
    print(f"Loc:    lat={summary.location['lat']}, lon={summary.location['lon']}")
    print("")

    if summary.sun:
        house_str = f"House {summary.sun.house}" if summary.sun.house is not None else "House ?"
        print(f"Sun:  {summary.sun.signed_dms} ({house_str})")
        if summary.sun.declination_dms:
            print(f"      decl: {summary.sun.declination_dms}")
    if summary.moon:
        house_str = f"House {summary.moon.house}" if summary.moon.house is not None else "House ?"
        print(f"Moon: {summary.moon.signed_dms} ({house_str})")
        if summary.moon.declination_dms:
            print(f"      decl: {summary.moon.declination_dms}")

    print("")
    print("Distributions")
    
    def _print_dist(label: str, dist: Any) -> None:
        if hasattr(dist, "items"):
            # Robust sorting: handle cases where values are dicts (not comparable in Py3)
            def _get_sort_score(val: Any) -> float:
                if isinstance(val, (int, float)):
                    return float(val)
                if isinstance(val, dict):
                    # Try to find a numeric 'count' or 'value'
                    for key in ("count", "value", "score", "weight"):
                        if key in val and isinstance(val[key], (int, float)):
                            return float(val[key])
                return 0.0

            items = sorted(dist.items(), key=lambda x: _get_sort_score(x[1]), reverse=True)

            # Formatter for display
            def _fmt_val(val: Any) -> str:
                if isinstance(val, dict) and "count" in val:
                    return str(val["count"])
                return str(val)

            formatted = ", ".join(f"{k}: {_fmt_val(v)}" for k, v in items)
            print(f"  {label:<10} {formatted}")
        else:
            print(f"  {label:<10} {dist}")

    _print_dist("element", summary.element_distribution)
    _print_dist("modality", summary.modality_distribution)

    print("")
    print("Aspects")
    for a in summary.aspects[:50]:
        print(f"  {a.body1} {a.symbol} {a.body2} (orb: {a.orb})")

    print("")
    print("Houses")
    for h in summary.houses:
        line = f"  House {h.id}: {h.dms} {h.sign}"
        if h.declination_dms:
            line += f" (decl: {h.declination_dms})"
        print(line)


def _to_jsonable(summary: ChartSummaryOut) -> Dict[str, Any]:
    raw = asdict(summary)
    return raw


def main(argv: List[str]) -> int:
    try:
        inp = _parse_args(argv)
        chart, dt_utc_iso = _build_chart(inp)
        summary = _to_summary(chart, inp, dt_utc_iso)

        if inp.output_format in ("text", "both"):
            _print_text(summary)

        if inp.output_format in ("json", "both"):
            payload = _to_jsonable(summary)
            print(json.dumps(payload, ensure_ascii=False, indent=2))

        return 0
    except Exception as exc:
        print(f"[nataly plugin] Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
