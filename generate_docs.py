import json

with open('openapi_dump.json', 'r', encoding='utf-8') as f:
    spec = json.load(f)

with open('endpoints_documentation.md', 'w', encoding='utf-8') as out:
    out.write('# Endpoints del Backend (`VehiculosRC`)\n')
    out.write('A continuación se detallan los endpoints disponibles, sus métodos, y la estructura esperada para request/response. Esto servirá de contexto para integrar el frontend con Gemini.\n\n')

    schemas = spec.get('components', {}).get('schemas', {})

    def get_schema_details(ref_path):
        schema_name = ref_path.split('/')[-1]
        if schema_name in schemas:
            s = schemas[schema_name]
            props = s.get('properties', {})
            req = s.get('required', [])
            fields = []
            for p, d in props.items():
                req_str = '*' if p in req else ''
                ptype = d.get('type', 'any')
                if 'format' in d: ptype += f" ({d['format']})"
                fields.append(f'{p}{req_str}: {ptype}')
            return f'{schema_name} {{ ' + ', '.join(fields) + ' }}'
        return schema_name

    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            summary = details.get('summary', 'Sin descripcion')
            
            request_schema = 'None'
            if 'requestBody' in details:
                try:
                    content = details['requestBody'].get('content', {})
                    if 'application/json' in content:
                        schema = content['application/json']['schema']
                        if '$ref' in schema:
                            request_schema = get_schema_details(schema['$ref'])
                        else:
                            request_schema = 'Estructura JSON personalizada'
                    elif 'multipart/form-data' in content:
                        request_schema = 'Form Data (Archivos/multipart)'
                    else:
                        request_schema = 'Otro formato'
                except KeyError:
                    request_schema = 'Formatos variables'
                    
            response_schema = 'None'
            if 'responses' in details and '200' in details['responses']:
                try:
                    content = details['responses']['200'].get('content', {})
                    if 'application/json' in content:
                        schema = content['application/json']['schema']
                        if '$ref' in schema:
                            response_schema = get_schema_details(schema['$ref'])
                        elif schema.get('type') == 'array' and '$ref' in schema.get('items', {}):
                            response_schema = 'List[ ' + get_schema_details(schema['items']['$ref']) + ' ]'
                        else:
                            response_schema = schema.get('type', 'any')
                    elif 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content:
                         response_schema = 'Archivo Excel (.xlsx)'
                    elif 'application/pdf' in content:
                         response_schema = 'Archivo PDF'
                    elif not content:
                         response_schema = 'Cuerpo vacio'
                except KeyError:
                    response_schema = 'Otros formatos'

            out.write(f'### {method.upper()} `{path}`\n')
            out.write(f'**Propósito:** {summary}\n')
            out.write(f'- **Payload (Body) que se envía:** `{request_schema}`\n')
            out.write(f'- **Respuesta (Response) que se recibe:** `{response_schema}`\n\n')
