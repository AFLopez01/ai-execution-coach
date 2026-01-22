"""
Generador de reportes semanales en Markdown

Este módulo proporciona funcionalidad para generar reportes semanales detallados
que analicen el Execution Score, actividades realizadas y recomendaciones.
"""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from .score_calculator import calculate_daily_score, classify_score


def calculate_weekly_metrics(daily_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calcula las métricas agregadas de una semana a partir de los logs diarios.
    
    Args:
        daily_logs: Lista de diccionarios de logs diarios
    
    Returns:
        Diccionario con métricas semanales
    """
    total_activities = 0
    activities_with_output = 0
    total_time_minutes = 0
    production_time = 0
    consumption_time = 0
    daily_scores: List[float] = []
    
    for log in daily_logs:
        if 'activities' not in log:
            continue
        
        activities = log['activities']
        total_activities += len(activities)
        
        day_score = calculate_daily_score(log)
        daily_scores.append(day_score)
        
        for activity in activities:
            # Contar actividades con output
            output = activity.get('output_produced', 'none')
            if output and str(output).lower().strip() != 'none':
                activities_with_output += 1
            
            # Sumar tiempo invertido (acepta ambos nombres de campos)
            time_invested = activity.get('time_invested_minutes') or activity.get('duration_minutes', 0)
            total_time_minutes += time_invested
            
            # Clasificar por tipo
            activity_type = activity.get('type', 'both').lower()
            
            if activity_type == 'production':
                production_time += time_invested
            elif activity_type == 'consumption':
                consumption_time += time_invested
            else:  # 'both' o learning
                # Para actividades mixtas, dividir el tiempo según si tiene output
                if output and str(output).lower().strip() != 'none':
                    production_time += time_invested
                else:
                    consumption_time += time_invested
    
    # Calcular porcentajes
    production_percentage = (production_time / total_time_minutes * 100) if total_time_minutes > 0 else 0
    consumption_percentage = (consumption_time / total_time_minutes * 100) if total_time_minutes > 0 else 0
    
    # Calcular score semanal promedio
    weekly_score = (sum(daily_scores) / len(daily_scores)) if daily_scores else 0
    
    return {
        'total_activities': total_activities,
        'activities_with_output': activities_with_output,
        'total_time_minutes': total_time_minutes,
        'total_time_hours': round(total_time_minutes / 60, 2),
        'production_time': production_time,
        'consumption_time': consumption_time,
        'production_percentage': round(production_percentage, 1),
        'consumption_percentage': round(consumption_percentage, 1),
        'weekly_score': round(weekly_score, 2),
        'daily_scores': daily_scores
    }


def generate_weekly_report(daily_logs: List[Dict[str, Any]], user_name: str = "User") -> str:
    """
    Genera el reporte semanal detallado en formato Markdown.
    
    Args:
        daily_logs: Lista de diccionarios con logs diarios
        user_name: Nombre del usuario para personalizar el reporte
    
    Returns:
        String con el reporte en Markdown
    """
    
    metrics = calculate_weekly_metrics(daily_logs)
    score = metrics['weekly_score']
    classification = classify_score(score)
    
    # Determinar veredicto
    if classification == "EXCELENTE":
        verdict = "EXCELENTE - Sigue así"
    elif classification == "ACEPTABLE":
        verdict = "ACEPTABLE - Límite inferior, cuidado"
    else:
        verdict = "FRACASO - Acción inmediata requerida"
    
    # Generar reporte
    report = f"""# Reporte Semanal de Ejecución - {user_name}

## 1. Resumen Ejecutivo
- *Tiempo total invertido:* {metrics['total_time_minutes']} minutos ({metrics['total_time_hours']} horas)
- *Ratio consumo vs producción:* {metrics['consumption_percentage']}% consumo / {metrics['production_percentage']}% producción
- *Veredicto general:* *{verdict}*
- *Execution Score:* {score:.1f}/100

## 2. Execution Score
*Fórmula aplicada:*  
(Actividades con output real / Total de actividades) × 100

- Total de actividades: {metrics['total_activities']}
- Actividades con output real: {metrics['activities_with_output']}

*Cálculo:*  
({metrics['activities_with_output']} / {metrics['total_activities']}) × 100 = *{score:.1f}*

*Clasificación:* *{classification}*
"""
    
    if classification == "FRACASO":
        report += "⚠️ *ALERTA CRÍTICA:* Debes eliminar todo consumo pasivo inmediatamente la próxima semana.\n"
    elif classification == "ACEPTABLE":
        report += "⚠️ *ADVERTENCIA:* Estás en el límite. Un tropiezo más y caes en fracaso.\n"
    else:
        report += "✅ *EXCELENTE:* Mantén este ritmo de ejecución.\n"
    
    report += f"""
## 3. Desglose por Tipo de Actividad

- *Consumo puro (sin output):*  
  {metrics['consumption_time']} min → *{metrics['consumption_percentage']}%*
- *Producción directa:*  
  {metrics['production_time']} min → *{metrics['production_percentage']}%*

**Dato clave:** {'pasaste MÁS tiempo consumiendo que produciendo' if metrics['consumption_percentage'] > metrics['production_percentage'] else 'produjiste más de lo que consumiste'}

## 4. Scores Diarios
"""
    
    for i, score in enumerate(metrics['daily_scores'], 1):
        score_class = classify_score(score)
        report += f"- Día {i}: {score:.1f}/100 ({score_class})\n"
    
    report += f"""
## 5. Recomendaciones

"""
    
    if score < 60:
        report += """- ❌ **ACCIÓN INMEDIATA:** Debes enfocar TODO en actividades con output tangible
- Minimiza o elimina el consumo de contenido sin objetivo claro
- Define objetivos claros antes de cada actividad
- Registra QÜÉÉ produciste en cada sesión
"""
    elif score < 80:
        report += """- ⚠️ **MEJORA NECESARIA:** Incrementa las actividades productivas
- Reduce el consumo de contenido sin propósito
- Sé más selectivo con qué consumes
- Asegúrate de extraer valor de cada actividad
"""
    else:
        report += """- ✅ **CONTINÚA:** Mantén este balance
- Tu ritmo de ejecución es sostenible
- Sigue documentando outputs de forma clara
- Considera compartir tu metodología con otros
"""
    
    report += f"""

---
*Reporte generado:* {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    return report


def save_weekly_report(report_content: str, output_dir: str, user_name: str = "user") -> str:
    """
    Guarda el reporte semanal en un archivo Markdown.
    
    Args:
        report_content: Contenido del reporte en Markdown
        output_dir: Directorio donde guardar el reporte
        user_name: Nombre del usuario para el nombre del archivo
    
    Returns:
        Ruta del archivo guardado
    """
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Crear nombre de archivo con timestamp
    filename = f"week-{user_name}.md"
    file_path = output_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return str(file_path)


if __name__ == "__main__":
    # Ejemplo de uso
    sample_logs: List[Dict[str, Any]] = [
        {
            "date": "2026-01-12",
            "activities": [
                {
                    "type": "consumption",
                    "description": "Podcast",
                    "time_invested_minutes": 60,
                    "output_produced": "none"
                },
                {
                    "type": "production",
                    "description": "Coding",
                    "time_invested_minutes": 120,
                    "output_produced": "module.py"
                }
            ],
            "self_assessment": {
                "honesty_score": 8,
                "main_blocker": "Distracciones",
                "tomorrow_commitment": "Enfoque total"
            }
        },
        {
            "date": "2026-01-13",
            "activities": [
                {
                    "type": "production",
                    "description": "Writing",
                    "time_invested_minutes": 90,
                    "output_produced": "draft.md"
                }
            ],
            "self_assessment": {
                "honesty_score": 9,
                "main_blocker": "Ninguno",
                "tomorrow_commitment": "Completar draft"
            }
        }
    ]
    
    report = generate_weekly_report(sample_logs, "TestUser")
    print(report)
    print("\n" + "="*50)
    print(f"Reporte guardado en: {save_weekly_report(report, 'data/weekly_reports', 'testuser')}")