"""
AI Execution Coach - Main Entry Point
Sistema de accountability basado en outputs reales, no en consumo de información.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys
from dotenv import load_dotenv

load_dotenv()

# Importar módulos del proyecto
from core.log_validator import validate_daily_log
from core.score_calculator import calculate_weekly_score, classify_score
from core.report_generator import generate_weekly_report, calculate_weekly_metrics

# Para integración con OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI no instalado. Instala con: pip install openai")

# Configuración de rutas
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DAILY_LOGS_DIR = DATA_DIR / "daily_logs"
WEEKLY_REPORTS_DIR = DATA_DIR / "weekly_reports"
CONFIG_FILE = DATA_DIR / "user_config.json"
PROMPTS_DIR = BASE_DIR / "prompts"

# Crear directorios si no existen
for directory in [DATA_DIR, DAILY_LOGS_DIR, WEEKLY_REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class ExecutionCoach:
    """Clase principal del AI Execution Coach"""
    
    def __init__(self):
        self.config = self.load_config()
        self.today = datetime.now().date()
        
        # Inicializar OpenAI si está disponible
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                self.openai_client = None
                print("⚠️  OPENAI_API_KEY no encontrada en variables de entorno")
        else:
            self.openai_client = None
    
    def load_config(self) -> Dict:
        """Carga la configuración del usuario"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save_config(self, config: Dict):
        """Guarda la configuración del usuario"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def setup_initial_config(self):
        """Configuración inicial o modificación de objetivo semanal"""
        print("\n" + "="*60)
        print("⚙️  CONFIGURACIÓN DE OBJETIVO SEMANAL")
        print("="*60 + "\n")
        
        # Si ya existe config, solo modificar objetivo
        if self.config:
            print(f"📌 Objetivo actual: {self.config.get('weekly_goal', 'No definido')}")
            print(f"🎯 Tipo de enfoque: {self.config.get('focus_type', 'No definido')}")
            modify = input("\n¿Deseas modificar el objetivo semanal? (s/n): ").lower()
            
            if modify != 's':
                return
            
            print("\n🔄 Modificando objetivo semanal...\n")
            self.config['weekly_goal'] = input("Nuevo objetivo semanal: ").strip()
            
        else:
            # Primera configuración
            print("👤 Nombre: ", end="")
            user_name = input().strip()
            
            print("\n🎯 Tipos de enfoque disponibles:")
            focus_types = ["proyecto", "publicaciones", "repos", "tech_skills", "language_skills"]
            for i, ft in enumerate(focus_types, 1):
                print(f"  {i}. {ft}")
            
            focus_choice = input("\nSelecciona el tipo de enfoque (1-5): ").strip()
            focus_type = focus_types[int(focus_choice) - 1] if focus_choice.isdigit() and 1 <= int(focus_choice) <= 5 else "proyecto"
            
            print("\n📅 Días de reporte semanal:")
            print("  1. 5 días (Lunes a Viernes)")
            print("  2. 7 días (Toda la semana)")
            report_choice = input("\nSelecciona (1-2): ").strip()
            report_days = 5 if report_choice == "1" else 7
            
            weekly_goal = input("\n🎯 Define tu objetivo semanal: ").strip()
            
            self.config = {
                "user_name": user_name,
                "weekly_goal": weekly_goal,
                "focus_type": focus_type,
                "report_days": report_days,
                "start_date": self.today.isoformat()
            }
        
        self.save_config(self.config)
        print("\n✅ Configuración guardada correctamente\n")
    
    def register_daily_log(self):
        """Registra las actividades del día"""
        print("\n" + "="*60)
        print(f"📝 REGISTRO DEL DÍA - {self.today.strftime('%Y-%m-%d')}")
        print("="*60 + "\n")
        
        # Verificar si ya existe log para hoy
        daily_log_path = DAILY_LOGS_DIR / f"{self.today.isoformat()}.json"
        existing_log = None
        
        if daily_log_path.exists():
            with open(daily_log_path, 'r', encoding='utf-8') as f:
                existing_log = json.load(f)
            
            print("⚠️  Ya existe un registro para hoy.")
            print(f"   Actividades registradas: {len(existing_log.get('activities', []))}")
            choice = input("\n¿Qué deseas hacer? (1) Agregar más actividades (2) Reemplazar todo: ").strip()
            
            if choice != "1" and choice != "2":
                print("❌ Opción inválida")
                return
            
            if choice == "2":
                existing_log = None
        
        # Inicializar estructura
        if existing_log:
            daily_log = existing_log
        else:
            daily_log = {
                "date": self.today.isoformat(),
                "activities": [],
                "self_assessment": {}
            }
        
        # Registrar actividades
        print("\n📋 Registra tus actividades del día")
        print("   (Escribe 'fin' cuando termines de agregar actividades)\n")
        
        while True:
            activity_name = input("🔹 Nombre de la actividad: ").strip()
            if activity_name.lower() == 'fin':
                break
            
            # Duración
            while True:
                duration_input = input("⏱️  Tiempo invertido (minutos): ").strip()
                if duration_input.isdigit():
                    duration_minutes = int(duration_input)
                    break
                print("   ⚠️  Por favor ingresa un número válido")
            
            # Output producido
            output_produced = input("📦 Output producido (escribe 'none' si no hubo): ").strip()
            
            # Determinar tipo
            if output_produced.lower() == 'none':
                activity_type = "consumption"
                activity = {
                    "name": activity_name,
                    "duration_minutes": duration_minutes,
                    "output_produced": output_produced,
                    "type": activity_type
                }
            else:
                print("\n   Tipo de actividad:")
                print("   1. Producción")
                print("   2. Consumo + Producción (mixed)")
                type_choice = input("   Selecciona (1-2): ").strip()
                activity_type = "production" if type_choice == "1" else "both"
                
                # Solicitar evidencia
                evidence = input("🔗 Link o path de evidencia: ").strip()
                
                # Validar evidencia real
                validation_result = self.validate_evidence(evidence, activity_type)
                if not validation_result:
                    print("   ⚠️  Advertencia: No se pudo validar la evidencia")
                    confirm = input("   ¿Continuar de todas formas? (s/n): ").lower()
                    if confirm != 's':
                        print("   ❌ Actividad cancelada")
                        continue
                
                activity = {
                    "name": activity_name,
                    "duration_minutes": duration_minutes,
                    "output_produced": output_produced,
                    "type": activity_type,
                    "evidence": evidence
                }
            
            daily_log["activities"].append(activity)
            print("   ✅ Actividad registrada\n")
        
        # Auto-evaluación
        if not daily_log["activities"]:
            print("\n⚠️  No se registraron actividades")
            return
        
        print("\n" + "-"*60)
        print("🎯 AUTO-EVALUACIÓN DEL DÍA")
        print("-"*60 + "\n")
        
        while True:
            honesty_input = input("📊 Calificación honesta del día (1-10): ").strip()
            if honesty_input.isdigit() and 1 <= int(honesty_input) <= 10:
                honesty_score = int(honesty_input)
                break
            print("   ⚠️  Ingresa un número entre 1 y 10")
        
        main_obstacle = input("🚧 Principal obstáculo del día: ").strip()
        commitment_tomorrow = input("🎯 Compromiso para mañana: ").strip()
        
        daily_log["self_assessment"] = {
            "honesty_score": honesty_score,
            "main_obstacle": main_obstacle,
            "commitment_tomorrow": commitment_tomorrow
        }
        
        # Guardar temporalmente para validar
        with open(str(daily_log_path) + ".temp", 'w', encoding='utf-8') as f:
            json.dump(daily_log, f, indent=2, ensure_ascii=False)
        
        # Validar estructura del log usando el módulo log_validator
        is_valid, error = validate_daily_log(str(daily_log_path) + ".temp")
        
        # Limpiar archivo temporal
        if os.path.exists(str(daily_log_path) + ".temp"):
            os.remove(str(daily_log_path) + ".temp")
        
        if not is_valid:
            print(f"\n❌ Error en la validación del log: {error}")
            return
        
        # Guardar log
        with open(daily_log_path, 'w', encoding='utf-8') as f:
            json.dump(daily_log, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Registro del día guardado: {daily_log_path.name}")
        print(f"   📌 {len(daily_log['activities'])} actividades registradas\n")
    
    def validate_evidence(self, evidence: str, activity_type: str) -> bool:
        """Valida que la evidencia sea real (archivo existe, URL accesible, etc.)"""
        # Validar path local
        if os.path.exists(evidence):
            return True
        
        # Validar URL (básico)
        if evidence.startswith(('http://', 'https://', 'github.com', 'gitlab.com')):
            return True
        
        # Validar si es un path relativo válido
        project_path = BASE_DIR / evidence
        if project_path.exists():
            return True
        
        return False
    
    def view_weekly_summary(self):
        """Muestra resumen de la semana actual sin análisis LLM"""
        print("\n" + "="*60)
        print("📊 RESUMEN DE LA SEMANA ACTUAL")
        print("="*60 + "\n")
        
        # Obtener logs de la semana
        week_logs = self.get_current_week_logs()
        
        if not week_logs:
            print("⚠️  No hay registros para esta semana\n")
            return
        
        # Calcular estadísticas usando calculate_weekly_metrics
        metrics = calculate_weekly_metrics(week_logs)
        
        print(f"📅 Días registrados: {len(week_logs)}/{self.config.get('report_days', 7)}")
        print(f"⏱️  Tiempo total: {metrics['total_time_minutes']} minutos ({metrics['total_time_hours']} horas)")
        print(f"📋 Total actividades: {metrics['total_activities']}")
        print(f"✅ Actividades con output: {metrics['activities_with_output']}")
        print(f"📈 Score semanal: {metrics['weekly_score']:.1f}/100")
        print(f"📊 Clasificación: {classify_score(metrics['weekly_score'])}")
        print(f"🔄 Producción: {metrics['production_percentage']:.1f}% | Consumo: {metrics['consumption_percentage']:.1f}%\n")
    
    def get_current_week_logs(self) -> List[Dict]:
        """Obtiene todos los logs de la semana actual"""
        week_logs = []
        report_days = self.config.get('report_days', 7)
        
        # Calcular inicio de semana (lunes)
        days_since_monday = self.today.weekday()
        week_start = self.today - timedelta(days=days_since_monday)
        
        for i in range(report_days):
            log_date = week_start + timedelta(days=i)
            
            # Si report_days=5, saltar sábados y domingos
            if report_days == 5 and log_date.weekday() >= 5:
                continue
            
            log_path = DAILY_LOGS_DIR / f"{log_date.isoformat()}.json"
            
            if log_path.exists():
                with open(log_path, 'r', encoding='utf-8') as f:
                    week_logs.append(json.load(f))
        
        return week_logs
    
    def generate_weekly_report_with_llm(self):
        """Genera reporte semanal completo con análisis de LLM"""
        print("\n" + "="*60)
        print("🤖 GENERANDO REPORTE SEMANAL CON ANÁLISIS IA")
        print("="*60 + "\n")
        
        # Obtener logs de la semana
        week_logs = self.get_current_week_logs()
        
        if not week_logs:
            print("⚠️  No hay suficientes registros para generar reporte\n")
            return
        
        print(f"📊 Procesando {len(week_logs)} días de registro...")
        
        # Generar reporte base con report_generator
        base_report = generate_weekly_report(
            week_logs, 
            self.config.get('user_name', 'User')
        )
        
        print("✅ Reporte base generado")
        
        # Cargar prompt para LLM
        prompt_path = PROMPTS_DIR / "prompt_weekly_report.md"
        
        if not prompt_path.exists():
            print(f"⚠️  No se encontró el prompt en: {prompt_path}")
            llm_analysis = "⚠️  Análisis LLM no disponible (prompt no encontrado)"
        else:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            
            # Enviar a OpenAI
            if self.openai_client:
                print("🤖 Enviando a OpenAI para análisis profundo...\n")
                llm_analysis = self.get_llm_analysis(base_report, prompt_template, week_logs)
            else:
                print("⚠️  OpenAI no configurado. Generando reporte sin análisis IA\n")
                llm_analysis = "⚠️  Análisis LLM no disponible (OpenAI no configurado)"
        
        # Guardar reporte completo
        week_start = self.today - timedelta(days=self.today.weekday())
        report_filename = f"weekly_report_{week_start.isoformat()}.md"
        report_path = WEEKLY_REPORTS_DIR / report_filename
        
        full_report = base_report + "\n\n" + "="*60 + "\n"
        full_report += "## 🤖 ANÁLISIS DE IA Y CONFRONTACIÓN\n"
        full_report += "="*60 + "\n\n"
        full_report += llm_analysis
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(full_report)
        
        print(f"✅ Reporte completo generado: {report_filename}")
        print(f"📁 Ubicación: {report_path}\n")
        
        # Sistema de decisiones automáticas
        self.apply_automatic_decisions(week_logs)
    
    def get_llm_analysis(self, base_report: str, prompt_template: str, week_logs: List[Dict]) -> str:
        """Envía el reporte a OpenAI para análisis"""
        if not self.openai_client:
            return "⚠️  Cliente OpenAI no inicializado"
        
        try:
            # Preparar el contexto completo
            logs_json = json.dumps(week_logs, indent=2, ensure_ascii=False)
            
            # Construir el prompt completo
            full_prompt = f"""{prompt_template}

## DATOS DE LA SEMANA:

### Reporte Base Generado:
{base_report}

### Logs Diarios Completos (JSON):
```json
{logs_json}
```

Genera ahora el análisis profundo siguiendo el formato especificado en el prompt inicial.
"""
            
            # Llamar a OpenAI
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "Eres un auditor implacable pero constructivo que analiza la ejecución semanal de actividades. Tu trabajo es detectar autoengaño y promover ejecución real con outputs tangibles."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error al obtener análisis de OpenAI: {str(e)}"
    
    def apply_automatic_decisions(self, week_logs: List[Dict]):
        """Aplica decisiones automáticas basadas en el score"""
        execution_score = calculate_weekly_score(week_logs)
        
        print("\n" + "="*60)
        print("⚙️  DECISIONES AUTOMÁTICAS DEL SISTEMA")
        print("="*60 + "\n")
        
        print(f"📊 Execution Score: {execution_score:.1f}/100")
        print(f"📈 Clasificación: {classify_score(execution_score)}\n")
        
        if execution_score < 50:
            print("🔴 Score < 50 → REDUCIENDO OBJETIVO")
            self.reduce_weekly_goal()
            print("⚠️  LÍMITE DE CONSUMO: Máximo 30% del tiempo en actividades sin output")
        elif execution_score < 60:
            print("🟡 Score < 60 → Mantener objetivo con advertencia")
            print("⚠️  LÍMITE DE CONSUMO: Máximo 40% del tiempo en actividades sin output")
        elif execution_score >= 70:
            print("🟢 Score ≥ 70 → Mantener enfoque, considerar aumentar dificultad")
            print("✅ Buen balance entre consumo y producción")
        else:
            print("🟡 Score entre 60-69 → Mantener objetivo con límites de consumo")
            print("⚠️  Estás en el límite. Aumenta producción la próxima semana")
        
        print()
    
    def reduce_weekly_goal(self):
        """Reduce el objetivo semanal y lo guarda"""
        reduced_goal_path = DATA_DIR / "weekly_goal_reduced.json"
        
        reduced_goal = {
            "original_goal": self.config.get('weekly_goal'),
            "reduced_goal": f"[REDUCIDO 50%] {self.config.get('weekly_goal', 'Sin objetivo')}",
            "reduction_date": self.today.isoformat(),
            "reason": "Execution Score < 50",
            "action_required": "Eliminar todo consumo pasivo + enfoque en outputs mínimos"
        }
        
        with open(reduced_goal_path, 'w', encoding='utf-8') as f:
            json.dump(reduced_goal, f, indent=2, ensure_ascii=False)
        
        # Actualizar config
        self.config['weekly_goal'] = reduced_goal['reduced_goal']
        self.save_config(self.config)
        
        print(f"   📝 Nuevo objetivo: {reduced_goal['reduced_goal']}")
        print(f"   📄 Detalles guardados en: {reduced_goal_path.name}")
    
    def view_reports_history(self):
        """Muestra historial de reportes semanales"""
        print("\n" + "="*60)
        print("📚 HISTORIAL DE REPORTES SEMANALES")
        print("="*60 + "\n")
        
        reports = sorted(WEEKLY_REPORTS_DIR.glob("weekly_report_*.md"), reverse=True)
        
        if not reports:
            print("⚠️  No hay reportes generados aún\n")
            return
        
        for i, report_path in enumerate(reports, 1):
            print(f"{i}. {report_path.name}")
        
        print("\n0. Volver")
        choice = input("\nSelecciona un reporte para ver (0 para volver): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(reports):
            with open(reports[int(choice) - 1], 'r', encoding='utf-8') as f:
                print("\n" + "="*60)
                print(f.read())
                print("="*60)
            input("\nPresiona Enter para continuar...")
        print()
    
    def run(self):
        """Ejecuta el menú principal"""
        # Verificar si existe configuración
        if not self.config:
            print("\n👋 Bienvenido a AI Execution Coach")
            print("   Primero necesitamos configurar tu objetivo semanal\n")
            self.setup_initial_config()
        
        while True:
            print("\n" + "="*60)
            print("🎯 AI EXECUTION COACH - MENÚ PRINCIPAL")
            print("="*60)
            print(f"\n👤 Usuario: {self.config.get('user_name', 'No configurado')}")
            print(f"🎯 Objetivo: {self.config.get('weekly_goal', 'No definido')}")
            print(f"📅 Hoy: {self.today.strftime('%A, %d de %B de %Y')}\n")
            
            print("1. Configurar objetivo semanal (primera vez o cambio)")
            print("2. Registrar día de hoy")
            print("3. Ver resumen de la semana actual")
            print("4. Generar reporte semanal (con análisis LLM)")
            print("5. Ver historial de reportes")
            print("6. Salir")
            
            choice = input("\nSelecciona una opción (1-6): ").strip()
            
            if choice == "1":
                self.setup_initial_config()
            elif choice == "2":
                self.register_daily_log()
            elif choice == "3":
                self.view_weekly_summary()
            elif choice == "4":
                self.generate_weekly_report_with_llm()
            elif choice == "5":
                self.view_reports_history()
            elif choice == "6":
                print("\n👋 ¡Recuerda: Si no hay output, no hubo aprendizaje!\n")
                break
            else:
                print("\n❌ Opción inválida. Intenta de nuevo.\n")


def main():
    """Punto de entrada principal"""
    try:
        coach = ExecutionCoach()
        coach.run()
    except KeyboardInterrupt:
        print("\n\n👋 Saliendo... Recuerda ejecutar, no solo aprender.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()