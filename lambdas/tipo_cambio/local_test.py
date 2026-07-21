import sys
import os
import json

# Add current directory to path to allow importing local files
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lambda_function import lambda_handler

def main():
    print("==================================================")
    print("  SIMULANDO EJECUCIÓN LOCAL DE AWS LAMBDA  ")
    print("==================================================")
    print("Ejecutando lambda_handler(event={}, context=None)...")
    
    event = {}
    context = None
    
    response = lambda_handler(event, context)
    
    print("\n----------------- RESPUESTA -----------------")
    print(f"Status Code: {response['statusCode']}")
    
    try:
        body = json.loads(response['body'])
        print("Cuerpo de Respuesta (JSON):")
        print(json.dumps(body, indent=4, ensure_ascii=False))
    except Exception as e:
        print("Cuerpo de Respuesta (Raw):")
        print(response['body'])
        print(f"Error parseando JSON: {e}")
    print("==================================================")

if __name__ == "__main__":
    main()
