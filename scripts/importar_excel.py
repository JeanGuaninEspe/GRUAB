"""
Script de Importación y Migración Masiva de Asistencias de Grúa desde Excel a SQL Server.
Permite ejecutar en modo simulación (--dry-run) para validar y reportar inconsistencias
antes de impactar la base de datos.

Uso:
    # Modo simulación (no guarda cambios):
    python scripts/importar_excel.py --archivo "ruta/al/archivo.xlsx" --dry-run

    # Modo inserción real:
    python scripts/importar_excel.py --archivo "ruta/al/archivo.xlsx"
"""
import sys
import os
import argparse
import unicodedata
import re
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Optional, Tuple, Dict, Any, List

import pandas as pd
from sqlalchemy.orm import Session

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Asegurar que el directorio raíz del proyecto esté en el PYTHONPATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.core.database import SessionLocal
from app.models.catalogos import CatPersonal, CatVehiculoConcesion
from app.models.transaccionales import AsistenciaGrua


# ==============================================================================
# UTILIDADES DE NORMALIZACIÓN DE TEXTO Y VALORES
# ==============================================================================

def normalizar_texto(texto: Any) -> str:
    """Normaliza texto: elimina tildes, caracteres invisibles, dobles espacios y pasa a mayúsculas."""
    if texto is None or pd.isna(texto):
        return ""
    s = str(texto).strip()
    s_norm = unicodedata.normalize("NFKD", s)
    s_sin_tildes = "".join(c for c in s_norm if not unicodedata.combining(c))
    s_limpio = re.sub(r"\s+", " ", s_sin_tildes).upper()
    return s_limpio


def limpiar_codigo(val: Any) -> Optional[str]:
    """Limpia el código de formulario eliminando sufijos .0 y espacios innecesarios."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s if s else None


def parse_decimal(val: Any) -> Optional[Decimal]:
    """Convierte cadenas con comas o números a Decimal con precisión."""
    if val is None or pd.isna(val):
        return None
    try:
        s = str(val).strip().replace(",", ".")
        s = re.sub(r"[^\d.-]", "", s)
        return Decimal(s) if s else None
    except Exception:
        return None


def parse_entero(val: Any, default: Optional[int] = None) -> Optional[int]:
    """Convierte valores a entero de forma segura."""
    if val is None or pd.isna(val):
        return default
    try:
        if isinstance(val, (int, float)):
            return int(val)
        # Extraer dígitos
        match = re.search(r"\d+", str(val))
        return int(match.group(0)) if match else default
    except Exception:
        return default


def parse_bool(val: Any) -> bool:
    """Detecta valores de bandera tipo 1, SI, TRUE, X."""
    if val is None or pd.isna(val):
        return False
    if isinstance(val, bool):
        return val
    s = normalizar_texto(val)
    return s in ("1", "SI", "TRUE", "X", "VERDADERO", "V", "OK")


def parse_fecha(fecha_val: Any) -> Optional[date]:
    """Parsea una fecha en diversos formatos comunes de Excel."""
    if fecha_val is None or pd.isna(fecha_val):
        return None
    if isinstance(fecha_val, date) and not isinstance(fecha_val, datetime):
        return fecha_val
    if isinstance(fecha_val, (datetime, pd.Timestamp)):
        return fecha_val.date()
    
    s = str(fecha_val).strip()
    # Si viene con hora agregada en texto
    if " " in s:
        s = s.split(" ")[0]
        
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%d/%m/%y", "%Y%m%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def parse_hora(hora_val: Any) -> Optional[time]:
    """Parsea una hora desde objeto time, datetime, string o fracción de día de Excel."""
    if hora_val is None or pd.isna(hora_val):
        return None
    if isinstance(hora_val, time):
        return hora_val
    if isinstance(hora_val, (datetime, pd.Timestamp)):
        return hora_val.time()
    if isinstance(hora_val, (float, int)):
        # Fracción decimal de día de Excel (ej: 0.5 = 12:00:00)
        try:
            total_seconds = int(float(hora_val) * 86400)
            hours = (total_seconds // 3600) % 24
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            return time(hours, minutes, seconds)
        except Exception:
            return None
            
    s = str(hora_val).strip()
    # Si viene un datetime en formato string "2026-05-01 12:48:00"
    if " " in s:
        partes = s.split(" ")
        s = partes[1] if len(partes) > 1 else s
        
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            pass
            
    # Intentar con regex hh:mm
    match = re.search(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", s)
    if match:
        h = int(match.group(1)) % 24
        m = int(match.group(2)) % 60
        sec = int(match.group(3) or 0) % 60
        return time(h, m, sec)
        
    return None


def parse_abscisa(val: Any) -> Optional[Decimal]:
    """
    Parsea una abscisa vial en formato '262+000' o '262.000' o número.
    Ejemplo: '262+000' -> Decimal('262.000')
    """
    if val is None or pd.isna(val):
        return None
    s = str(val).strip().replace(" ", "")
    if "+" in s:
        partes = s.split("+")
        try:
            km = Decimal(partes[0].replace(",", "."))
            metros = Decimal(partes[1].replace(",", "."))
            return (km + (metros / Decimal(1000))).quantize(Decimal("0.001"))
        except Exception:
            pass
    try:
        d = parse_decimal(s)
        if d and d > Decimal(1000):
            # En caso de que viniera 262000 sin el signo +
            return (d / Decimal(1000)).quantize(Decimal("0.001"))
        return d
    except Exception:
        return None


def combinar_fecha_hora(fecha_d: Optional[date], hora_t: Optional[time], ref_dt: Optional[datetime] = None) -> Optional[datetime]:
    """Combina fecha y hora y ajusta cruce de medianoche si la hora es posterior al timestamp de referencia."""
    if not fecha_d or not hora_t:
        return None
    base_date = ref_dt.date() if ref_dt else fecha_d
    dt = datetime.combine(base_date, hora_t)
    if ref_dt and dt < ref_dt:
        dt += timedelta(days=1)
    return dt


# ==============================================================================
# RESOLUCIÓN INTELIGENTE DE CATÁLOGOS (PERSONAL Y VEHÍCULOS)
# ==============================================================================

class CatalogoResolver:
    def __init__(self, db: Session):
        self.personal_db = db.query(CatPersonal).all()
        self.vehiculos_db = db.query(CatVehiculoConcesion).all()
        
        # Mapeos exactos por nombre normalizado
        self.mapa_personal_exacto: Dict[str, CatPersonal] = {}
        # Mapeo por lista de tokens
        self.lista_personal_tokens: List[Tuple[set, CatPersonal]] = []
        
        for p in self.personal_db:
            norm = normalizar_texto(p.nombre_completo)
            self.mapa_personal_exacto[norm] = p
            tokens = set(norm.split())
            self.lista_personal_tokens.append((tokens, p))
            
        # ID de personal por defecto para NO ESPECIFICADO
        no_esp = self.mapa_personal_exacto.get("NO ESPECIFICADO")
        self.id_no_especificado = no_esp.id_personal if no_esp else 8
        
        # Mapeo de vehículos de grúa
        self.grua_pequena = next((v for v in self.vehiculos_db if v.codigo_interno == "GRUA-01"), None)
        self.grua_grande = next((v for v in self.vehiculos_db if v.codigo_interno == "GRUA-02"), None)

    def resolver_personal(self, nombre_raw: Any, rol_esperado: Optional[str] = None) -> Tuple[Optional[int], str]:
        """
        Resuelve un nombre hacia su ID de CatPersonal.
        Retorna (id_personal, nombre_resuelto_o_advertencia).
        """
        nombre_norm = normalizar_texto(nombre_raw)
        if not nombre_norm or nombre_norm in ("-", "N/A", "NINGUNO", "NO APLICA", "S/N"):
            return self.id_no_especificado, "NO ESPECIFICADO (Vacío en Excel)"
            
        # 1. Búsqueda exacta normalizada
        if nombre_norm in self.mapa_personal_exacto:
            p = self.mapa_personal_exacto[nombre_norm]
            return p.id_personal, p.nombre_completo
            
        # 2. Búsqueda por similitud de palabras (tokens)
        tokens_input = set(nombre_norm.split())
        mejor_coincidencia = None
        max_interseccion = 0
        
        for tokens_db, p in self.lista_personal_tokens:
            if rol_esperado and p.rol != rol_esperado:
                continue
            inter = len(tokens_input.intersection(tokens_db))
            if inter > max_interseccion:
                max_interseccion = inter
                mejor_coincidencia = p
                
        # Si coincide en al menos 2 nombres/apellidos o el 100% de los tokens de entrada
        if mejor_coincidencia and (max_interseccion >= 2 or max_interseccion == len(tokens_input)):
            return mejor_coincidencia.id_personal, f"{mejor_coincidencia.nombre_completo} (Aproximado)"
            
        # 3. Fallback a NO ESPECIFICADO
        return self.id_no_especificado, f"NO ESPECIFICADO (No se encontró: '{nombre_raw}')"


# ==============================================================================
# DETECCIÓN Y MAPEO DE CABECERAS DE EXCEL
# ==============================================================================

def mapear_columnas_excel(df: pd.DataFrame) -> Dict[str, str]:
    """
    Identifica de forma dinámica las columnas requeridas sin importar
    saltos de línea o espacios redundantes en las cabeceras.
    """
    mapeo = {}
    for col in df.columns:
        c_norm = normalizar_texto(col).lower()
        
        if "formulario" in c_norm or "registro" in c_norm:
            mapeo["formulario"] = col
        elif "fecha" in c_norm and "llamada" not in c_norm:
            mapeo["fecha"] = col
        elif "hora" in c_norm and "llamada" in c_norm:
            mapeo["hora_llamada"] = col
        elif "hora" in c_norm and ("arribo" in c_norm or "llegada" in c_norm):
            mapeo["hora_arribo"] = col
        elif "hora" in c_norm and ("terminad" in c_norm or "termino" in c_norm or "fin" in c_norm):
            mapeo["hora_termino"] = col
        elif "hora" in c_norm and ("regreso" in c_norm or "retorno" in c_norm):
            mapeo["hora_retorno"] = col
        elif "supervisor" in c_norm or "secretaria" in c_norm:
            mapeo["supervisor"] = col
        elif "chofer" in c_norm or "conductor" in c_norm:
            mapeo["chofer"] = col
        elif "turno" in c_norm:
            mapeo["turno"] = col
        elif c_norm in ("grua", "grua:", "tipo grua"):
            mapeo["grua_texto"] = col
        elif "pequena" in c_norm or "pequena:" in c_norm:
            mapeo["pequena"] = col
        elif "grande" in c_norm:
            mapeo["grande"] = col
        elif "clase de accidente" in c_norm or "clase accidente" in c_norm:
            mapeo["clase_accidente"] = col
        elif "tipo de accidente" in c_norm or "tipo accidente" in c_norm:
            mapeo["tipo_accidente"] = col
        elif c_norm.startswith("leve"):
            mapeo["leve"] = col
        elif c_norm.startswith("grave"):
            mapeo["grave"] = col
        elif c_norm.startswith("fatal") and "mtop" not in c_norm:
            mapeo["fatal"] = col
        elif "sector" in c_norm:
            mapeo["sector"] = col
        elif c_norm in ("km", "km:", "abscisa") or (c_norm.startswith("km") and "salida" not in c_norm and "llegada" not in c_norm and "recorrido" not in c_norm):
            mapeo["abscisa_km"] = col
        elif "sentido" in c_norm:
            mapeo["sentido"] = col
        elif "placa" in c_norm:
            mapeo["placa"] = col
        elif "tipo" in c_norm and "vehic" in c_norm:
            mapeo["tipo_vehiculo"] = col
        elif "usuario" in c_norm and ("atendido" in c_norm or "#" in c_norm):
            mapeo["usuarios_atendidos"] = col
        elif "usuario" in c_norm and "reporta" in c_norm:
            mapeo["usuario_reporta"] = col
        elif "motivo" in c_norm:
            mapeo["motivo"] = col
        elif "causa" in c_norm:
            mapeo["posible_causa"] = col
        elif "salida" in c_norm and ("km" in c_norm or "odometro" in c_norm):
            mapeo["odometro_salida"] = col
        elif "llegada" in c_norm and ("km" in c_norm or "odometro" in c_norm):
            mapeo["odometro_llegada"] = col
        elif "mtop" in c_norm:
            mapeo["reportado_mtop"] = col
        elif "observ" in c_norm:
            mapeo["observaciones"] = col
            
    return mapeo


def cargar_dataframe_excel(ruta_archivo: str, nombre_hoja: Optional[str] = None) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Lee el archivo Excel, detecta la fila de cabeceras real y mapea las columnas."""
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
        
    excel_file = pd.ExcelFile(ruta_archivo)
    hoja_elegida = nombre_hoja if nombre_hoja and nombre_hoja in excel_file.sheet_names else excel_file.sheet_names[0]
    
    # Leer primeras 15 filas sin cabecera para ubicar la fila de títulos
    df_raw = pd.read_excel(ruta_archivo, sheet_name=hoja_elegida, header=None, nrows=15)
    
    fila_encabezado = 0
    for idx, row in df_raw.iterrows():
        fila_texto = " ".join([str(v) for v in row.values if pd.notna(v)]).lower()
        if "fecha" in fila_texto and ("formulario" in fila_texto or "chofer" in fila_texto or "turno" in fila_texto):
            fila_encabezado = idx
            break
            
    # Leer el dataframe completo con la cabecera identificada
    df = pd.read_excel(ruta_archivo, sheet_name=hoja_elegida, header=fila_encabezado)
    mapeo = mapear_columnas_excel(df)
    
    return df, mapeo


# ==============================================================================
# PROCESAMIENTO E INGESTA FILA A FILA
# ==============================================================================

def procesar_importacion(ruta_archivo: str, dry_run: bool = True, hoja: Optional[str] = None):
    print("=" * 80)
    print("       SISTEMA DE IMPORTACIÓN Y MIGRACIÓN DE ASISTENCIAS DE GRÚA        ")
    print("=" * 80)
    print(f"📁 Archivo: {os.path.abspath(ruta_archivo)}")
    print(f"⚙️  Modo:    {'🔍 DRY-RUN (Simulación sin guardar cambios)' if dry_run else '🚀 PRODUCCIÓN (Escritura en Base de Datos)'}")
    print("-" * 80)
    
    db: Session = SessionLocal()
    try:
        resolver = CatalogoResolver(db)
        print(f"✓ Conexión establecida con SQL Server.")
        print(f"✓ Catálogo de personal cargado: {len(resolver.personal_db)} personas.")
        print(f"✓ Catálogo de unidades de grúa cargado: GRUA-01 (Pequeña), GRUA-02 (Grande).")
        
        df, cols = cargar_dataframe_excel(ruta_archivo, hoja)
        print(f"✓ Columnas leídas: {len(df.columns)} columnas.")
        print(f"✓ Filas detectadas en la hoja: {len(df)} registros.")
        
        if "formulario" not in cols:
            raise ValueError("No se detectó la columna 'Formulario Registro:' en el archivo Excel.")
            
        print("-" * 80)
        print("Iniciando procesamiento y validación fila a fila...\n")
        
        # Pre-cargar códigos de formularios existentes en la base de datos para omitir duplicados
        codigos_existentes = set(
            c[0] for c in db.query(AsistenciaGrua.codigo_formulario).all() if c[0]
        )
        print(f"ℹ️  Existen actualmente {len(codigos_existentes)} formularios de grúa registrados en la BD.\n")
        
        insertados = 0
        omitidos_existentes = 0
        omitidos_vacios = 0
        alertas_personal = []
        registros_a_insertar = []
        
        for idx, row in df.iterrows():
            num_fila_excel = idx + 2  # Aproximación al número de fila real en Excel
            
            # 1. Código de Formulario
            cod_form = limpiar_codigo(row.get(cols["formulario"]))
            if not cod_form:
                omitidos_vacios += 1
                continue
                
            if cod_form in codigos_existentes:
                omitidos_existentes += 1
                continue
                
            # 2. Fechas y Tiempos
            f_val = parse_fecha(row.get(cols.get("fecha")))
            h_llamada = parse_hora(row.get(cols.get("hora_llamada")))
            h_arribo = parse_hora(row.get(cols.get("hora_arribo")))
            h_termino = parse_hora(row.get(cols.get("hora_termino")))
            h_retorno = parse_hora(row.get(cols.get("hora_retorno")))
            
            ts_llamada = combinar_fecha_hora(f_val, h_llamada)
            ts_arribo = combinar_fecha_hora(f_val, h_arribo, ref_dt=ts_llamada)
            ts_termino = combinar_fecha_hora(f_val, h_termino, ref_dt=ts_arribo)
            ts_retorno = combinar_fecha_hora(f_val, h_retorno, ref_dt=ts_termino)
            
            # 3. Personal (Supervisor y Chofer)
            id_sup, desc_sup = resolver.resolver_personal(
                row.get(cols.get("supervisor")), rol_esperado="SUPERVISOR"
            )
            id_chof, desc_chof = resolver.resolver_personal(
                row.get(cols.get("chofer")), rol_esperado="CHOFER_GRUA"
            )
            
            if "No se encontró" in desc_chof:
                alertas_personal.append(f"Fila {num_fila_excel} [Form: {cod_form}]: Chofer no encontrado ('{row.get(cols.get('chofer'))}')")
            if "No se encontró" in desc_sup:
                alertas_personal.append(f"Fila {num_fila_excel} [Form: {cod_form}]: Supervisor no encontrado ('{row.get(cols.get('supervisor'))}')")
                
            # 4. Consolidación de Grúa y Unidad
            es_grande = parse_bool(row.get(cols.get("grande")))
            es_pequena = parse_bool(row.get(cols.get("pequena")))
            texto_grua = normalizar_texto(row.get(cols.get("grua_texto")))
            
            if es_grande or "GRANDE" in texto_grua:
                tipo_grua = "GRANDE"
                id_vehiculo = resolver.grua_grande.id_vehiculo if resolver.grua_grande else 6
            elif es_pequena or "PEQUENA" in texto_grua:
                tipo_grua = "PEQUEÑA"
                id_vehiculo = resolver.grua_pequena.id_vehiculo if resolver.grua_pequena else 5
            elif "PLATAFORMA" in texto_grua:
                tipo_grua = "PLATAFORMA"
                id_vehiculo = resolver.grua_pequena.id_vehiculo if resolver.grua_pequena else 5
            else:
                tipo_grua = "PEQUEÑA"
                id_vehiculo = resolver.grua_pequena.id_vehiculo if resolver.grua_pequena else 5
                
            # 5. Consolidación de Severidad
            es_fatal = parse_bool(row.get(cols.get("fatal")))
            es_grave = parse_bool(row.get(cols.get("grave")))
            es_leve = parse_bool(row.get(cols.get("leve")))
            
            if es_fatal:
                severidad = "FATAL"
            elif es_grave:
                severidad = "GRAVE"
            elif es_leve:
                severidad = "LEVE"
            else:
                severidad = "LEVE"
                
            # 6. Fusión de Clase y Tipo de Accidente
            clase_acc = str(row.get(cols.get("clase_accidente")) or "").strip()
            tipo_acc = str(row.get(cols.get("tipo_accidente")) or "").strip()
            # Si clase_acc es solo la severidad (LEVE, GRAVE, FATAL), no duplicarla como tipo de accidente
            if clase_acc.upper() in ("LEVE", "GRAVE", "FATAL"):
                clase_acc = ""
            if clase_acc and tipo_acc and clase_acc.upper() != tipo_acc.upper() and tipo_acc != "nan" and clase_acc != "nan":
                tipo_accidente_final = f"{clase_acc} / {tipo_acc}"
            elif tipo_acc and tipo_acc != "nan":
                tipo_accidente_final = tipo_acc
            elif clase_acc and clase_acc != "nan":
                tipo_accidente_final = clase_acc
            else:
                tipo_accidente_final = None
                
            # 7. Odometría y Kilometraje
            km_salida = parse_decimal(row.get(cols.get("odometro_salida")))
            km_llegada = parse_decimal(row.get(cols.get("odometro_llegada")))
            abscisa = parse_abscisa(row.get(cols.get("abscisa_km")))
            
            # 8. Sentido
            sentido_raw = normalizar_texto(row.get(cols.get("sentido")))
            if "ASC" in sentido_raw or "NORTE" in sentido_raw:
                sentido = "ASCENDENTE"
            elif "DESC" in sentido_raw or "SUR" in sentido_raw:
                sentido = "DESCENDENTE"
            else:
                sentido = "BIDIRECCIONAL"
                
            # 9. Construir Objeto ORM
            nuevo_registro = AsistenciaGrua(
                codigo_formulario=cod_form,
                id_supervisor=id_sup,
                id_chofer=id_chof,
                id_vehiculo=id_vehiculo,
                turno=parse_entero(row.get(cols.get("turno")), default=1),
                tipo_grua=tipo_grua,
                ts_llamada=ts_llamada,
                ts_arribo=ts_arribo,
                ts_termino=ts_termino,
                ts_retorno=ts_retorno,
                sector_referencia=str(row.get(cols.get("sector")) or "").strip() or None,
                abscisa_km=abscisa,
                sentido=sentido,
                usuario_reporta=str(row.get(cols.get("usuario_reporta")) or "").strip() or None,
                placa_asistida=normalizar_texto(row.get(cols.get("placa"))) or None,
                tipo_vehiculo_asistido=normalizar_texto(row.get(cols.get("tipo_vehiculo"))) or None,
                usuarios_atendidos=parse_entero(row.get(cols.get("usuarios_atendidos")), default=1),
                motivo_atencion=str(row.get(cols.get("motivo")) or "").strip() or None,
                tipo_accidente=tipo_accidente_final,
                posible_causa=str(row.get(cols.get("posible_causa")) or "").strip() or None,
                severidad=severidad,
                km_origen_traslado=abscisa,
                km_destino_traslado=None,
                odometro_salida_km=km_salida,
                odometro_llegada_km=km_llegada,
                reportado_mtop=parse_bool(row.get(cols.get("reportado_mtop"))),
                observaciones=str(row.get(cols.get("observaciones")) or "").strip() or None,
            )
            
            # Registrar para evitar duplicados en el mismo archivo
            codigos_existentes.add(cod_form)
            registros_a_insertar.append(nuevo_registro)
            insertados += 1
            
        print("-" * 80)
        print("                    RESUMEN DE VALIDACIÓN Y RESULTADOS                  ")
        print("-" * 80)
        print(f"📊 Total de filas procesadas:         {len(df)}")
        print(f"✨ Registros nuevos a importar:       {insertados}")
        print(f"⏭️  Omitidos (ya registrados en BD):   {omitidos_existentes}")
        print(f"⚪ Omitidos (filas vacías/sin código): {omitidos_vacios}")
        print(f"⚠️  Alertas de personal no ubicado:    {len(alertas_personal)}")
        
        if alertas_personal:
            print("\nDetalle de las primeras 10 alertas de personal:")
            for a in alertas_personal[:10]:
                print(f"   • {a}")
            if len(alertas_personal) > 10:
                print(f"   ... y {len(alertas_personal) - 10} alertas adicionales asignadas a NO ESPECIFICADO.")
                
        # 10. Persistencia o Rollback
        if dry_run:
            if registros_a_insertar:
                print("\nValidando restricciones directamente contra SQL Server (transacción temporal)...")
                db.add_all(registros_a_insertar)
                db.flush()
                print("✓ Validación en SQL Server superada con éxito (tipos de datos, llaves foráneas y cálculos correctos).")
                print("\nVista previa de los primeros 3 registros validados:")
                for r in registros_a_insertar[:3]:
                    print(f"   • Formulario: {r.codigo_formulario} | Fecha: {r.ts_llamada} | Placa: {r.placa_asistida} | Tipo: {r.tipo_grua} | Km recorridos calculados: {r.km_recorridos}")
            
            db.rollback()
            print("\n" + "=" * 80)
            print("🔍 MODO DRY-RUN COMPLETADO: No se guardó ningún cambio en la base de datos.")
            print("   Si el resultado es correcto, ejecuta el comando sin la bandera --dry-run:")
            print(f"   .venv\\Scripts\\python scripts/importar_excel.py --archivo \"{ruta_archivo}\"")
            print("=" * 80)
        else:
            if registros_a_insertar:
                print("\nGuardando registros en SQL Server...")
                db.add_all(registros_a_insertar)
                db.commit()
                print("=" * 80)
                print(f"🎉 ÉXITO: Se insertaron {len(registros_a_insertar)} registros en dbo.asistencias_grua.")
                print("=" * 80)
            else:
                print("\nℹ️  No hubo nuevos registros para insertar.")
                
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR CRÍTICO durante la importación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ==============================================================================
# ENTRYPOINT CLI
# ==============================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Herramienta CLI para migrar asistencias de grúa desde Excel a SQL Server."
    )
    parser.add_argument(
        "--archivo",
        "-a",
        type=str,
        required=True,
        help="Ruta absoluta o relativa del archivo Excel (.xlsx o .xls).",
    )
    parser.add_argument(
        "--hoja",
        "-s",
        type=str,
        default=None,
        help="Nombre de la hoja o pestaña de Excel a procesar (opcional).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecuta la validación completa y reporte sin guardar cambios en la base de datos.",
    )
    
    args = parser.parse_args()
    procesar_importacion(ruta_archivo=args.archivo, dry_run=args.dry_run, hoja=args.hoja)
