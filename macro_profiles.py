from dataclasses import dataclass
from typing import Dict

@dataclass
class MacroProfile:
    name: str
    display_name: str
    has_extra_tags: bool = False
    cost_precision: int = 1
    skip_stages_offset: int = 0  

#Registro estricto de perfiles soportados (basados en 2 verdades absolutas)
MACRO_REGISTRY: Dict[str, MacroProfile] = {
    'MacroPLP_I_20220414': MacroProfile(
        name='MacroPLP_I_20220414',
        display_name='Macro 20220414 (v5.0)',
        has_extra_tags=False,
        skip_stages_offset=4  
    ),
    'MacroPLP_I_20250508': MacroProfile(
        name='MacroPLP_I_20250508',
        display_name='Macro 20250508 (v6.3)',
        has_extra_tags=True,
        skip_stages_offset=0
    )
}

def get_profile(name: str) -> MacroProfile:
    """Retorna el perfil por nombre o el estándar si no se encuentra."""
    if name not in MACRO_REGISTRY:
        print(f"Advertencia: Perfil '{name}' no encontrado. Usando MacroPLP_I_20250508 por defecto.")
    return MACRO_REGISTRY.get(name, MACRO_REGISTRY['MacroPLP_I_20250508'])
