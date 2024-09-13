from .tonercontroler import one_toner
from .sectorcontroler import one_sector

def validar_salida_toner(toner_id, sector_id, cantidad):
    toner = one_toner(toner_id)
    sector = one_sector(sector_id)

    if toner_id and sector and cantidad is None:
        return False
    elif cantidad > toner.cantidad_actual or cantidad <= 0:
        return False
    else:
        return True
    
def validar_entrada_toner(toner_id, cantidad):
    toner = one_toner(toner_id)

    if toner_id and cantidad is None:
        return False
    elif cantidad <= 0:
        return False
    else:
        return True
    
def validar_entrada_sector(sector_name, duracion_predefinida):
    sector_existe = one_sector(sector_name)
    if sector_existe is not None:
        return False
    if duracion_predefinida < 0:
        return False
    else:
        return True
    
