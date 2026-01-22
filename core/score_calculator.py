"""
Módulo para calcular el Execution Score basado en actividades con output tangible.

El Execution Score mide el porcentaje de actividades que generaron un output
tangible (cualquier valor diferente a "none").
"""

from typing import Dict, List, Any, cast


def calculate_daily_score(daily_log_dict: Dict[str, Any]) -> float:
    """
    Calcula el Execution Score para un día específico.
    
    El score se calcula como:
    (Actividades con output tangible / Total de actividades) × 100
    
    Args:
        daily_log_dict: Diccionario con el log diario parseado desde JSON.
                       Debe contener la clave 'activities' con una lista de actividades.
    
    Returns:
        Score entre 0 y 100 representando el porcentaje de actividades
        con output tangible.
    
    Raises:
        KeyError: Si el diccionario no contiene la clave 'activities'.
        ValueError: Si 'activities' no es una lista.
    
    Example:
        >>> daily_log = {
        ...     "date": "2025-01-17",
        ...     "activities": [
        ...         {"task": "Coding", "output_produced": "module.py"},
        ...         {"task": "Meeting", "output_produced": "none"},
        ...         {"task": "Writing", "output_produced": "draft.md"}
        ...     ]
        ... }
        >>> calculate_daily_score(daily_log)
        66.67
    """
    if 'activities' not in daily_log_dict:
        raise KeyError("El diccionario debe contener la clave 'activities'")
    
    activities_raw: Any = daily_log_dict['activities']
    
    if not isinstance(activities_raw, list):
        raise ValueError("'activities' debe ser una lista")
    
    activities: List[Dict[str, Any]] = cast(List[Dict[str, Any]], activities_raw)
    
    # Caso edge: sin actividades
    if len(activities) == 0:
        return 0.0
    
    total_activities = len(activities)
    activities_with_output = 0
    
    for activity in activities:
        # Verificar si existe el campo output_produced
        output: Any = activity.get('output_produced', 'none')
        
        # Contar si NO es "none" (case-insensitive para robustez)
        if output and str(output).lower().strip() != 'none':
            activities_with_output += 1
    
    score = (activities_with_output / total_activities) * 100
    return round(score, 2)


def calculate_weekly_score(list_of_daily_logs: List[Dict[str, Any]]) -> float:
    """
    Calcula el Execution Score promedio para una semana.
    
    Args:
        list_of_daily_logs: Lista de diccionarios, cada uno representando
                           el log de un día.
    
    Returns:
        Score promedio semanal entre 0 y 100.
    
    Raises:
        ValueError: Si la lista está vacía.
    
    Example:
        >>> week_logs = [
        ...     {"activities": [{"output_produced": "file.py"}, {"output_produced": "none"}]},
        ...     {"activities": [{"output_produced": "doc.md"}, {"output_produced": "code.js"}]},
        ...     {"activities": [{"output_produced": "none"}, {"output_produced": "none"}]}
        ... ]
        >>> calculate_weekly_score(week_logs)
        50.0
    """
    if not list_of_daily_logs:
        raise ValueError("La lista de logs diarios no puede estar vacía")
    
    daily_scores: List[float] = []
    
    for daily_log in list_of_daily_logs:
        try:
            score = calculate_daily_score(daily_log)
            daily_scores.append(score)
        except (KeyError, ValueError) as e:
            # Log el error pero continuar con los demás días
            print(f"Advertencia: Error al procesar un log diario: {e}")
            continue
    
    if not daily_scores:
        raise ValueError("No se pudo calcular ningún score diario válido")
    
    weekly_score = sum(daily_scores) / len(daily_scores)
    return round(weekly_score, 2)


def classify_score(score: float) -> str:
    """
    Clasifica un Execution Score en categorías de desempeño.
    
    Args:
        score: Valor numérico del score entre 0 y 100.
    
    Returns:
        Clasificación del score:
        - "EXCELENTE" si score > 80
        - "ACEPTABLE" si 60 <= score <= 80
        - "FRACASO" si score < 60
    
    Example:
        >>> classify_score(85)
        'EXCELENTE'
        >>> classify_score(70)
        'ACEPTABLE'
        >>> classify_score(45)
        'FRACASO'
    """
    if score > 80:
        return "EXCELENTE"
    elif score >= 60:
        return "ACEPTABLE"
    else:
        return "FRACASO"