"""
Generador de reportes semanales en Markdown
"""

from typing import List, Dict
from datetime import datetime


def generate_weekly_report(weekly_data: Dict, score: float, classification: str) -> str:
    """
    Genera el reporte semanal en formato Markdown
    
    Args:
        weekly_data: Diccionario con datos de la semana
        score: Execution Score calculado
        classification: EXCELENTE/ACEPTABLE/FRACASO
    
    Returns:
        String con el reporte en Markdown
    """
    # TODO: Implementar generación con IA en Día 15-16
    # Por ahora, solo un template básico
    
    report = f"""# Weekly Execution Report

## Score: {score:.1f}/100 - {classification}

## Summary
- Total activities: {weekly_data.get('total_activities', 0)}
- Activities with output: {weekly_data.get('activities_with_output', 0)}

## Action Plan
{'CRITICAL: Eliminate all passive consumption next week' if score < 60 else 'Continue with current execution pace'}

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    return report


if __name__ == "__main__":
    # Ejemplo de uso
    sample_data = {
        'total_activities': 10,
        'activities_with_output': 7
    }
    print(generate_weekly_report(sample_data, 70.0, "ACEPTABLE"))