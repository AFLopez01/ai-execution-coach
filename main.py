"""
AI Execution Coach - Main Entry Point
"""

import argparse
from pathlib import Path
from core.log_validator import validate_daily_log
from core.score_calculator import calculate_daily_score
import json


def main():
    """Punto de entrada principal del programa"""
    parser = argparse.ArgumentParser(
        description='AI Execution Coach - Auditoría de ejecución vs consumo'
    )
    parser.add_argument(
        '--validate',
        type=str,
        help='Ruta al archivo daily_log.json para validar'
    )
    parser.add_argument(
        '--score',
        type=str,
        help='Ruta al archivo daily_log.json para calcular score'
    )
    
    args = parser.parse_args()
    
    if args.validate:
        is_valid, error = validate_daily_log(args.validate)
        if is_valid:
            print(f"✅ {args.validate} es válido")
        else:
            print(f"❌ Error: {error}")
    
    elif args.score:
        is_valid, error = validate_daily_log(args.score)
        if not is_valid:
            print(f"❌ Error: {error}")
            return
        
        with open(args.score, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        score = calculate_daily_score(data)
        print(f"📊 Daily Execution Score: {score:.1f}/100")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()