# fecha_chile.py — "hoy" SIEMPRE en hora de Chile, pase lo que pase con el reloj del PC.
# Motivo real (14-ago-2026): el Windows de Camilo quedó en zona horaria de Perth (UTC+8),
# así que en la tarde chilena date.today() ya devolvía el día siguiente y el panel se
# construía con la fecha equivocada. Nunca usar date.today() en este pipeline.
from datetime import datetime, timezone, timedelta

def _chile_offset(utc_dt):
    """Chile continental: UTC-3 en horario de verano (1er sáb sep → 1er sáb abr), UTC-4 el resto."""
    y = utc_dt.year
    def primer_sabado(anio, mes):
        d = datetime(anio, mes, 1, tzinfo=timezone.utc)
        return d + timedelta(days=(5 - d.weekday()) % 7)
    inicio_dst = primer_sabado(y, 9)     # septiembre: entra horario de verano
    fin_dst = primer_sabado(y, 4)        # abril: termina
    en_verano = utc_dt >= inicio_dst or utc_dt < fin_dst
    return timedelta(hours=-3 if en_verano else -4)

def ahora_chile():
    ahora_utc = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        return ahora_utc.astimezone(ZoneInfo("America/Santiago"))
    except Exception:
        return ahora_utc + _chile_offset(ahora_utc)   # sin tzdata: regla manual

def hoy_chile():
    return ahora_chile().date()

if __name__ == "__main__":
    from datetime import date
    print("date.today() del PC :", date.today())
    print("hoy en Chile        :", hoy_chile())
    print("ahora en Chile      :", ahora_chile().strftime("%Y-%m-%d %H:%M"))
