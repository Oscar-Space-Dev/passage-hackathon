"""Small deterministic research demonstrators; no execution of generated code."""
import math
from pydantic import Field, model_validator
from .schemas import StrictModel


class BatteryThermalInput(StrictModel):
    current_a: float = Field(ge=0, le=1000, allow_inf_nan=False)
    resistance_ohm: float = Field(ge=0, le=10, allow_inf_nan=False)
    heat_capacity_j_per_k: float = Field(gt=0, le=1000000, allow_inf_nan=False)
    cooling_w_per_k: float = Field(ge=0, le=1000, allow_inf_nan=False)
    ambient_c: float = Field(ge=-50, le=250, allow_inf_nan=False)
    initial_c: float = Field(ge=-50, le=250, allow_inf_nan=False)
    duration_s: float = Field(gt=0, le=7200, allow_inf_nan=False)
    step_s: float = Field(ge=0.001, le=60, allow_inf_nan=False)

    @model_validator(mode='after')
    def bounded(self):
        if math.ceil(self.duration_s / self.step_s) > 5000:
            raise ValueError('La simulation est limitée à 5 000 pas.')
        if self.step_s * self.cooling_w_per_k / self.heat_capacity_j_per_k > 0.5:
            raise ValueError('Le pas temporel est trop grand pour ce modèle.')
        return self


def battery_thermal(values: BatteryThermalInput):
    """Euler integration of C dT/dt = I²R - h(T-Ta), with explicit units."""
    p = values.model_dump()
    t, temperature = 0.0, values.initial_c
    series = [{'time_s': 0.0, 'temperature_c': round(temperature, 6)}]
    heat_w = values.current_a**2 * values.resistance_ohm
    while t < values.duration_s - 1e-9:
        dt = min(values.step_s, values.duration_s-t)
        temperature += dt * (heat_w-values.cooling_w_per_k*(temperature-values.ambient_c)) / values.heat_capacity_j_per_k
        t += dt
        if not math.isfinite(temperature) or abs(temperature) > 1000:
            raise ValueError('Température hors plage du modèle. Réduisez le courant ou le pas.')
        series.append({'time_s': round(t, 6), 'temperature_c': round(temperature, 6)})
    return {'model': 'thermal_rc_v1', 'parameters': p, 'heat_w': round(heat_w, 6),
            'final_c': round(temperature, 6),
            'max_c': max(row['temperature_c'] for row in series), 'series': series,
            'equation': 'C × dT/dt = I² × R − h × (T − T_amb)'}
