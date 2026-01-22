"""
AI Execution Coach - Log Validator Module
==========================================
Módulo para validar archivos de registro diario (daily_log.json) del sistema
AI Execution Coach. Verifica la estructura, tipos de datos y campos requeridos.

Autor: AI Execution Coach Team
Versión: 2.0 - Actualizado para estructura real del proyecto
"""

import json
import os
from pathlib import Path
from typing import Tuple, List, Dict, Any, cast

# Importar funciones del score_calculator
from .score_calculator import calculate_daily_score, classify_score


# Constantes de validación
VALID_ACTIVITY_TYPES = ["production", "consumption", "both"]
MIN_HONESTY_SCORE = 0
MAX_HONESTY_SCORE = 10


def validate_daily_log(file_path: str) -> Tuple[bool, str | None]:
    """
    Valida un archivo daily_log.json verificando estructura y campos requeridos.
    
    Estructura esperada:
    {
      "date": "YYYY-MM-DD",
      "activities": [
        {
          "name": "Nombre de la actividad",
          "duration_minutes": 120,
          "output_produced": "Descripción del output o 'none'",
          "type": "production" | "consumption" | "both"
        }
      ],
      "self_assessment": {
        "honesty_score": 0-10,
        "main_obstacle": "Descripción del obstáculo",
        "commitment_tomorrow": "Compromiso específico"
      }
    }
    
    Args:
        file_path (str): Ruta completa al archivo JSON a validar
        
    Returns:
        Tuple[bool, str | None]: 
            - (True, None) si el archivo es válido
            - (False, "mensaje de error") si hay algún problema
            
    Ejemplo:
        >>> is_valid, error = validate_daily_log("logs/2026-01-13.json")
        >>> if is_valid:
        ...     print("Archivo válido - Listo para análisis")
        ... else:
        ...     print(f"Error detectado: {error}")
    """
    
    # 1. Verificar que el archivo existe
    if not os.path.exists(file_path):
        return False, f"El archivo no existe: {file_path}"
    
    # 2. Verificar que es un archivo (no directorio)
    if not os.path.isfile(file_path):
        return False, f"La ruta no corresponde a un archivo: {file_path}"
    
    # 3. Intentar leer y parsear el JSON
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data: Any = json.load(f)
    except json.JSONDecodeError as e:
        return False, f"JSON inválido en línea {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error al leer archivo: {str(e)}"
    
    # 4. Verificar que data es un diccionario
    if not isinstance(data, dict):
        return False, "El JSON debe ser un objeto (diccionario), no una lista o valor primitivo"
    
    data = cast(Dict[str, Any], data)
    
    # 5. Verificar campos requeridos en el nivel superior
    required_fields = ['date', 'activities']
    for field in required_fields:
        if field not in data:
            return False, f"Campo requerido faltante en la raíz: '{field}'"
    
    # Verificar self_assessment (con ambos nombres posibles)
    if 'self_assessment' not in data and 'self_assesment' not in data:
        return False, "Campo requerido faltante en la raíz: 'self_assessment' o 'self_assesment'"
    
    # 6. Validar campo 'date'
    if not isinstance(data['date'], str):
        return False, "El campo 'date' debe ser un string (formato: YYYY-MM-DD)"
    
    if len(data['date']) != 10 or data['date'].count('-') != 2:
        return False, f"El campo 'date' debe tener formato YYYY-MM-DD, recibido: '{data['date']}'"
    
    # 7. Validar campo 'activities'
    if not isinstance(data['activities'], list):
        return False, "El campo 'activities' debe ser una lista/array"
    
    if len(data['activities']) == 0:
        return False, "El campo 'activities' no puede estar vacío (debe haber al menos 1 actividad)"
    
    # 8. Validar cada actividad individual
    # Aceptar ambos formatos de campos (legacy y nuevo)
    for idx, activity_raw in enumerate(data['activities'], start=1):
        if not isinstance(activity_raw, dict):
            return False, f"Actividad #{idx} debe ser un objeto/diccionario"
        
        activity: Dict[str, Any] = cast(Dict[str, Any], activity_raw)
        
        # Validar que tenga al menos descripción, tiempo y output
        has_description = any(k in activity for k in ['name', 'description'])
        has_time = any(k in activity for k in ['duration_minutes', 'time_invested_minutes'])
        has_output = 'output_produced' in activity
        has_type = 'type' in activity
        
        if not has_description:
            return False, f"Actividad #{idx}: debe tener 'name' o 'description'"
        
        if not has_time:
            return False, f"Actividad #{idx}: debe tener 'duration_minutes' o 'time_invested_minutes'"
        
        if not has_output:
            return False, f"Actividad #{idx}: campo requerido faltante 'output_produced'"
        
        if not has_type:
            return False, f"Actividad #{idx}: campo requerido faltante 'type'"
        
        # Validar tipos de datos
        if has_time:
            time_field = 'duration_minutes' if 'duration_minutes' in activity else 'time_invested_minutes'
            time_value = activity[time_field]
            if not isinstance(time_value, (int, float)):
                return False, f"Actividad #{idx}: '{time_field}' debe ser un número"
            if time_value <= 0:
                return False, f"Actividad #{idx}: '{time_field}' debe ser mayor a 0"
        
        # Validar output_produced
        if not isinstance(activity['output_produced'], str):
            return False, f"Actividad #{idx}: 'output_produced' debe ser string"
        
        # Validar type (puede ser 'production', 'consumption', 'both', 'learning')
        if not isinstance(activity['type'], str):
            return False, f"Actividad #{idx}: 'type' debe ser string"
        
        valid_types = VALID_ACTIVITY_TYPES + ['learning']  # Aceptar también 'learning'
        if activity['type'] not in valid_types:
            return False, f"Actividad #{idx}: 'type' debe ser uno de {valid_types}, recibido: '{activity['type']}'"
    
    # 9. Validar campo 'self_assessment' (con ambas grafías)
    assessment_raw: Any = data.get('self_assessment') or data.get('self_assesment')
    
    if not isinstance(assessment_raw, dict):
        return False, "El campo 'self_assessment' debe ser un objeto/diccionario"
    
    assessment: Dict[str, Any] = cast(Dict[str, Any], assessment_raw)
    
    # Validar campos en self_assessment (acepta ambos nombres de campos)
    # Buscar honesty_score
    honesty: Any = assessment.get('honesty_score')
    if honesty is None:
        return False, "self_assessment: campo requerido faltante 'honesty_score'"
    
    if not isinstance(honesty, (int, float)):
        return False, f"self_assessment: 'honesty_score' debe ser un número, recibido: {type(honesty).__name__}"
    
    if not (MIN_HONESTY_SCORE <= honesty <= MAX_HONESTY_SCORE):
        return False, f"self_assessment: 'honesty_score' debe estar entre {MIN_HONESTY_SCORE} y {MAX_HONESTY_SCORE}, recibido: {honesty}"
    
    # Buscar main obstacle/blocker (acepta ambos nombres)
    main_obstacle: Any = assessment.get('main_obstacle') or assessment.get('main_blocker')
    if main_obstacle is None:
        return False, "self_assessment: campo requerido faltante 'main_obstacle' o 'main_blocker'"
    
    if not isinstance(main_obstacle, str):
        return False, "self_assessment: 'main_obstacle' debe ser string"
    
    # Buscar commitment (acepta ambos nombres)
    commitment: Any = assessment.get('commitment_tomorrow') or assessment.get('tomorrow_commitment')
    if commitment is None:
        return False, "self_assessment: campo requerido faltante 'commitment_tomorrow' o 'tomorrow_commitment'"
    
    if not isinstance(commitment, str):
        return False, "self_assessment: 'commitment_tomorrow' debe ser string"
    
    # 10. Si pasó todas las validaciones
    return True, None


def validate_week_logs(folder_path: str) -> Dict[str, List[Any]]:
    """
    Valida todos los archivos JSON en una carpeta (una semana de logs).
    
    Args:
        folder_path (str): Ruta a la carpeta que contiene archivos JSON
        
    Returns:
        Dict[str, List[Any]]: Diccionario con dos listas:
            - 'valid': lista de rutas de archivos válidos
            - 'invalid': lista de tuplas (archivo, mensaje_error)
            
    Ejemplo:
        >>> results = validate_week_logs("logs/2026_week_02/")
        >>> print(f"✓ Válidos: {len(results['valid'])}")
        >>> print(f"✗ Inválidos: {len(results['invalid'])}")
        >>> 
        >>> # Procesar solo los válidos
        >>> for file_path in results['valid']:
        ...     process_log(file_path)
    """
    
    results: Dict[str, List[Any]] = {
        'valid': [],
        'invalid': []
    }
    
    # Verificar que la carpeta existe
    if not os.path.exists(folder_path):
        results['invalid'].append((folder_path, "La carpeta especificada no existe"))
        return results
    
    if not os.path.isdir(folder_path):
        results['invalid'].append((folder_path, "La ruta no corresponde a una carpeta"))
        return results
    
    # Obtener todos los archivos JSON en la carpeta
    folder = Path(folder_path)
    json_files = sorted(folder.glob('*.json'))  # Ordenados alfabéticamente
    
    if not json_files:
        print(f"⚠️  Advertencia: No se encontraron archivos JSON en '{folder_path}'")
        return results
    
    # Validar cada archivo JSON encontrado
    for json_file in json_files:
        file_path = str(json_file)
        is_valid, error_msg = validate_daily_log(file_path)
        
        if is_valid:
            results['valid'].append(file_path)
        else:
            results['invalid'].append((file_path, error_msg))
    
    return results


def analyze_execution_patterns(file_path: str) -> Dict[str, Any] | None:
    """
    Analiza patrones de ejecución vs consumo en un log validado.
    
    Esta función es específica del concepto AI Execution Coach:
    detecta si hay más consumo que producción.
    
    Args:
        file_path (str): Ruta al archivo JSON ya validado
        
    Returns:
        Dict con métricas de ejecución o None si el archivo es inválido
        
    Ejemplo:
        >>> metrics = analyze_execution_patterns("logs/2026-01-13.json")
        >>> print(f"Ratio ejecución: {metrics['execution_ratio']:.2%}")
        >>> print(f"Actividades sin output: {metrics['zero_output_count']}")
    """
    
    # Validar primero
    is_valid, error = validate_daily_log(file_path)
    if not is_valid:
        print(f"Error: {error}")
        return None
    
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Inicializar contadores
    total_minutes = 0
    production_minutes = 0
    consumption_minutes = 0
    both_minutes = 0
    activities_with_output = 0
    activities_without_output = 0
    
    # Analizar actividades
    for activity in data['activities']:
        duration = activity['duration_minutes']
        total_minutes += duration
        
        # Clasificar por tipo
        if activity['type'] == 'production':
            production_minutes += duration
        elif activity['type'] == 'consumption':
            consumption_minutes += duration
        elif activity['type'] == 'both':
            both_minutes += duration
        
        # Verificar si tiene output real
        output = activity['output_produced'].strip().lower()
        if output == 'none' or output == '':
            activities_without_output += 1
        else:
            activities_with_output += 1
    
    # Calcular métricas
    execution_ratio = (production_minutes + (both_minutes * 0.5)) / total_minutes if total_minutes > 0 else 0
    
    # Calcular Execution Score usando el módulo score_calculator
    execution_score = calculate_daily_score(data)
    score_classification = classify_score(execution_score)
    
    return {
        'date': data['date'],
        'total_minutes': total_minutes,
        'production_minutes': production_minutes,
        'consumption_minutes': consumption_minutes,
        'both_minutes': both_minutes,
        'execution_ratio': execution_ratio,
        'total_activities': len(data['activities']),
        'activities_with_output': activities_with_output,
        'zero_output_count': activities_without_output,
        'honesty_score': data['self_assessment']['honesty_score'],
        'main_obstacle': data['self_assessment']['main_obstacle'],
        'execution_score': execution_score,
        'score_classification': score_classification
    }


def generate_validation_report(results: Dict[str, List[Any]]) -> str:
    """
    Genera un reporte legible de los resultados de validación.
    
    Args:
        results (Dict[str, List[Any]]): Resultados de validate_week_logs()
        
    Returns:
        str: Reporte formateado como string
    """
    
    total = len(results['valid']) + len(results['invalid'])
    valid_count = len(results['valid'])
    invalid_count = len(results['invalid'])
    
    report: List[str] = []
    report.append("=" * 70)
    report.append("📊 REPORTE DE VALIDACIÓN - AI EXECUTION COACH")
    report.append("=" * 70)
    report.append(f"\n📁 Total de archivos analizados: {total}")
    report.append(f"✅ Archivos válidos: {valid_count}")
    report.append(f"❌ Archivos inválidos: {invalid_count}")
    
    if valid_count > 0:
        success_rate = (valid_count / total) * 100
        report.append(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if results['valid']:
        report.append("\n" + "-" * 70)
        report.append("✅ ARCHIVOS VÁLIDOS (listos para análisis)")
        report.append("-" * 70)
        for file_path in results['valid']:
            filename = os.path.basename(str(file_path))
            report.append(f"  ✓ {filename}")
    
    if results['invalid']:
        report.append("\n" + "-" * 70)
        report.append("❌ ARCHIVOS INVÁLIDOS (requieren corrección)")
        report.append("-" * 70)
        for item in results['invalid']:
            file_path, error = item
            filename = os.path.basename(str(file_path))
            report.append(f"  ✗ {filename}")
            report.append(f"    └─ Error: {error}")
    
    report.append("\n" + "=" * 70)
    
    return "\n".join(report)


def process_daily_logs_folder(logs_folder: str | None = None) -> Dict[str, Any]:
    """
    Procesa automáticamente todos los logs de la carpeta daily_logs_example.
    
    Args:
        logs_folder (str): Ruta a la carpeta de logs. Si no se proporciona,
                          busca automáticamente en ../data/daily_logs_example/
        
    Returns:
        Dict con análisis consolidado de todos los logs
        
    Ejemplo:
        >>> results = process_daily_logs_folder()
        >>> for log in results['analyzed_logs']:
        ...     print(f"{log['date']}: {log['execution_ratio']:.1%}")
    """
    
    # Si no se proporciona carpeta, buscar automáticamente
    if logs_folder is None:
        script_dir = Path(__file__).parent  # carpeta core/
        logs_folder = str(script_dir.parent / "data" / "daily_logs_example")
    
    logs_folder = str(logs_folder)  # Convertir a string por si es Path
    
    print(f"\n📂 Procesando carpeta: {logs_folder}\n")
    
    # Validar primero todos los archivos
    validation_results = validate_week_logs(logs_folder)
    
    print(generate_validation_report(validation_results))
    
    # Analizar solo los archivos válidos
    analyzed_logs: List[Dict[str, Any]] = []
    total_production = 0
    total_consumption = 0
    total_minutes = 0
    honesty_scores: List[float] = []
    execution_scores: List[float] = []
    
    if validation_results['valid']:
        print("\n📊 ANALIZANDO PATRONES DE EJECUCIÓN\n" + "-" * 70)
        
        for file_path in validation_results['valid']:
            metrics = analyze_execution_patterns(file_path)
            
            if metrics:
                analyzed_logs.append(metrics)
                total_production += metrics['production_minutes']
                total_consumption += metrics['consumption_minutes']
                total_minutes += metrics['total_minutes']
                honesty_scores.append(metrics['honesty_score'])
                execution_scores.append(metrics['execution_score'])
                
                # Mostrar resumen por archivo con Execution Score
                score_emoji = "🏆" if metrics['score_classification'] == "EXCELENTE" else "✅" if metrics['score_classification'] == "ACEPTABLE" else "⚠️"
                print(f"{score_emoji} {metrics['date']} | Score: {metrics['execution_score']:.1f} ({metrics['score_classification']})")
                print(f"   Ejecución: {metrics['execution_ratio']:.1%} | "
                      f"Output: {metrics['activities_with_output']}/{metrics['total_activities']} | "
                      f"Honestidad: {metrics['honesty_score']}/10")
    
    # Calcular estadísticas consolidadas
    avg_execution_score = sum(execution_scores) / len(execution_scores) if execution_scores else 0
    consolidated: Dict[str, Any] = {
        'total_days_analyzed': len(analyzed_logs),
        'total_days_invalid': len(validation_results['invalid']),
        'total_production_minutes': total_production,
        'total_consumption_minutes': total_consumption,
        'total_minutes': total_minutes,
        'average_execution_ratio': (total_production / total_minutes * 100) if total_minutes > 0 else 0,
        'average_honesty_score': sum(honesty_scores) / len(honesty_scores) if honesty_scores else 0,
        'average_execution_score': avg_execution_score,
        'execution_score_classification': classify_score(avg_execution_score),
        'analyzed_logs': analyzed_logs,
        'invalid_files': validation_results['invalid']
    }
    
    # Mostrar resumen consolidado
    print("\n" + "=" * 70)
    print("📈 RESUMEN CONSOLIDADO")
    print("=" * 70)
    print(f"Días analizados: {consolidated['total_days_analyzed']}")
    print(f"Días inválidos: {consolidated['total_days_invalid']}")
    print(f"Tiempo total: {consolidated['total_minutes']} minutos ({consolidated['total_minutes']//60}h)")
    print(f"Producción: {consolidated['total_production_minutes']} min")
    print(f"Consumo: {consolidated['total_consumption_minutes']} min")
    print(f"Ratio de ejecución promedio: {consolidated['average_execution_ratio']:.1f}%")
    print(f"Honestidad promedio: {consolidated['average_honesty_score']:.1f}/10")
    print(f"Execution Score promedio: {consolidated['average_execution_score']:.1f} ({consolidated['execution_score_classification']})")
    print("=" * 70)
    
    return consolidated


if __name__ == "__main__":
    """
    Demo completo del módulo log_validator con ejemplos del mundo real.
    Crea archivos de ejemplo y demuestra todas las funcionalidades.
    """
    
    print("🚀 AI EXECUTION COACH - Log Validator Demo\n")
    
    # ========================================================================
    # EJEMPLO 1: Crear archivo VÁLIDO (basado en tu estructura real)
    # ========================================================================
    print("1️⃣  Creando archivo de ejemplo VÁLIDO...")
    
    valid_log: Dict[str, Any] = {
        "date": "2026-01-13",
        "activities": [
            {
                "name": "Implementación del parser de logs JSON",
                "duration_minutes": 120,
                "output_produced": "Script log_parser.py con funciones de lectura y validación",
                "type": "production"
            },
            {
                "name": "Testing manual del parser",
                "duration_minutes": 35,
                "output_produced": "none",
                "type": "both"
            },
            {
                "name": "Lectura de documentación de pytest",
                "duration_minutes": 25,
                "output_produced": "none",
                "type": "consumption"
            },
            {
                "name": "Escritura de tests unitarios",
                "duration_minutes": 55,
                "output_produced": "Archivo test_parser.py con 8 tests",
                "type": "production"
            },
            {
                "name": "Reunión de sincronización con equipo",
                "duration_minutes": 45,
                "output_produced": "none",
                "type": "consumption"
            }
        ],
        "self_assessment": {
            "honesty_score": 9,
            "main_obstacle": "Falta de claridad en los requerimientos exactos del sistema de reportes",
            "commitment_tomorrow": "Definir y documentar los 3 reportes principales que necesito generar"
        }
    }
    
    # Crear carpeta de ejemplo
    os.makedirs("example_logs", exist_ok=True)
    
    # Guardar archivo válido
    valid_file = "example_logs/2026-01-13.json"
    with open(valid_file, 'w', encoding='utf-8') as f:
        json.dump(valid_log, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Archivo creado: {valid_file}\n")
    
    # ========================================================================
    # EJEMPLO 2: Validar archivo individual
    # ========================================================================
    print("2️⃣  Validando archivo individual...")
    is_valid, error = validate_daily_log(valid_file)
    
    if is_valid:
        print(f"   ✅ Validación exitosa: {valid_file}")
        print("   └─ El archivo cumple con todos los requisitos\n")
    else:
        print(f"   ❌ Validación fallida: {error}\n")
    
    # ========================================================================
    # EJEMPLO 3: Analizar patrones de ejecución
    # ========================================================================
    print("3️⃣  Analizando patrones de ejecución...")
    metrics = analyze_execution_patterns(valid_file)
    
    if metrics:
        print(f"   📊 Métricas del día {metrics['date']}:")
        print(f"   ├─ Tiempo total: {metrics['total_minutes']} minutos")
        print(f"   ├─ Producción: {metrics['production_minutes']} min")
        print(f"   ├─ Consumo: {metrics['consumption_minutes']} min")
        print(f"   ├─ Ratio de ejecución: {metrics['execution_ratio']:.1%}")
        print(f"   ├─ Actividades con output: {metrics['activities_with_output']}/{metrics['total_activities']}")
        print(f"   ├─ Execution Score: {metrics['execution_score']:.1f} ({metrics['score_classification']})")
        print(f"   └─ Honestidad: {metrics['honesty_score']}/10\n")
    
    # ========================================================================
    # EJEMPLO 4: Crear archivo INVÁLIDO para demostración
    # ========================================================================
    print("4️⃣  Creando archivos inválidos para demostración...")
    
    # Error 1: Campo faltante
    invalid_log_1: Dict[str, Any] = {
        "date": "2026-01-12",
        "activities": [
            {
                "name": "Actividad sin duration_minutes",
                "output_produced": "none",
                "type": "consumption"
            }
        ],
        "self_assessment": {
            "honesty_score": 7,
            "main_obstacle": "Procrastinación",
            "commitment_tomorrow": "Empezar a las 9am"
        }
    }
    
    invalid_file_1 = "example_logs/2026-01-12-invalid.json"
    with open(invalid_file_1, 'w', encoding='utf-8') as f:
        json.dump(invalid_log_1, f, indent=2)
    
    # Error 2: Tipo inválido
    invalid_log_2: Dict[str, Any] = {
        "date": "2026-01-11",
        "activities": [
            {
                "name": "Actividad con tipo incorrecto",
                "duration_minutes": 60,
                "output_produced": "Algo hecho",
                "type": "invalid_type"  # ❌ No es production/consumption/both
            }
        ],
        "self_assessment": {
            "honesty_score": 8,
            "main_obstacle": "Distracciones",
            "commitment_tomorrow": "Enfoque total"
        }
    }
    
    invalid_file_2 = "example_logs/2026-01-11-invalid.json"
    with open(invalid_file_2, 'w', encoding='utf-8') as f:
        json.dump(invalid_log_2, f, indent=2)
    
    print(f"   ✓ {invalid_file_1}")
    print(f"   ✓ {invalid_file_2}\n")
    
    # ========================================================================
    # EJEMPLO 5: Validar carpeta completa
    # ========================================================================
    print("5️⃣  Validando carpeta completa...")
    results = validate_week_logs("example_logs")
    
    # Generar y mostrar reporte
    report = generate_validation_report(results)
    print("\n" + report)
    
    # ========================================================================
    # EJEMPLO 6: Demostrar análisis de archivos inválidos
    # ========================================================================
    print("\n6️⃣  Demostrando detección de errores específicos...")
    
    for invalid_file in [invalid_file_1, invalid_file_2]:
        is_valid, error = validate_daily_log(invalid_file)
        filename = os.path.basename(invalid_file)
        print(f"\n   📄 {filename}")
        print(f"   └─ ❌ {error}")
    
    print("\n" + "=" * 70)
    print("✅ Demo completada exitosamente")
    print("📁 Revisa la carpeta 'example_logs/' para ver los archivos generados")
    print("=" * 70)
    
    # ========================================================================
    # BONUS: Procesar carpeta real de daily_logs_example si existe
    # ========================================================================
    print("\n\n🔄 INTEGRANDO CON ARCHIVOS REALES\n")
    
    # Intentar procesar la carpeta real de logs
    real_logs_dir = Path(__file__).parent.parent / "data" / "daily_logs_example"
    
    if real_logs_dir.exists() and any(real_logs_dir.glob('*.json')):
        print(f"✓ Se encontró carpeta de logs real: {real_logs_dir}")
        process_daily_logs_folder(str(real_logs_dir))
    else:
        print(f"⚠️  No se encontraron archivos JSON en: {real_logs_dir}")
        print("   Para procesar tus logs, ejecuta:")
        print(f"   process_daily_logs_folder('{real_logs_dir}')")