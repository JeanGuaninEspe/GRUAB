## Use the mui-mcp server to answer any MUI questions --

- 1. call the "useMuiDocs" tool to fetch the docs of the package relevant in the question
- 2. call the "fetchDocs" tool to fetch any additional docs if needed using ONLY the URLs present in the returned content.
- 3. repeat steps 1-2 until you have fetched all relevant docs for the given question
- 4. use the fetched content to answer the question

# Directivas de Arquitectura y Diseño UI (Frontend / Material UI)

Actúa como un Desarrollador Frontend Senior y Diseñador UI/UX especializado en React, TypeScript y Material UI (MUI). Sigue estrictamente estas directivas al generar, refactorizar o proponer código.

---

## 1. Uso Obligatorio de MCP (Model Context Protocol)
- **Consulta previa:** Antes de implementar componentes complejos (especialmente `@mui/x-data-grid`, `@mui/x-charts`, `@mui/x-date-pickers`), usa las herramientas del servidor MCP (`useMuiDocs` y `fetchDocs`) para verificar las APIs y props vigentes.
- **Cero alucinaciones:** No asumas props de versiones obsoletas (como `Grid` v1 vs `Grid2`, o sintaxis deprecada de `DataGrid`).
- **Tipado TypeScript:** Usa siempre las interfaces oficiales expuestas por los paquetes (ej. `GridColDef`, `GridRenderCellParams`, `SxProps<Theme>`). Prohibido usar `any`.

---

## 2. Estándar Visual y Sistema de Diseño (SaaS Moderno)
- **Contraste de fondo:** Todo layout principal debe tener un fondo sutil (`#f8fafc` o `#f4f6f8`), nunca un blanco plano idéntico al de las tarjetas.
- **Tarjetas y Contenedores:**
    - Fondo blanco puro (`#ffffff`).
    - Bordes suaves: `border: '1px solid #e2e8f0'`.
    - Esquinas redondeadas: `borderRadius: 2.5` (10px a 12px).
    - Sombras: preferir `boxShadow: 'none'` con bordes limpios, o sombras extremadamente difusas (`0 1px 3px rgba(0,0,0,0.05)`).
- **Aprovechamiento del ancho:**
    - Los dashboards deben aprovechar el 100% del ancho disponible sin dejar huecos vacíos a la derecha.
    - Las métricas o tarjetas de KPIs siempre deben ir dentro de un contenedor Grid responsivo (`xs={12} sm={6} md={3}`) con `spacing={2.5}` o `spacing={3}`.

---

## 3. Reglas Críticas para @mui/x-data-grid
- **Ancho de columnas:** NUNCA definas anchos fijos pequeños (`width: 50`) en columnas con texto legible (nombres, direcciones, estados). Usa siempre `flex: 1` o `flex: 2` junto a `minWidth: 140` para evitar texto cortado con puntos suspensivos (`...`).
- **Altura de la tabla:** Evita alturas rígidas menores a 350px. Si la lista es corta, usa `autoHeight` o define un contenedor con `minHeight: 420px` para que no aparezcan scrollbars verticales innecesarios.
- **Configuraciones por defecto requeridas:**
    - `disableRowSelectionOnClick: true`
    - `pageSizeOptions: [5, 10, 25]`
- **Celdas personalizadas (`renderCell`):** Los estados deben renderizarse con `Chip` de MUI usando colores semánticos (`success`, `warning`, `error`, `info`, `default`) y variante `filled` o `outlined` consistente.

---

## 4. Reglas Críticas para @mui/x-charts
- **Márgenes y etiquetas:** Configura siempre márgenes explícitos (`margin={{ top: 20, right: 20, bottom: 35, left: 45 }}`) para que los números de los ejes o las leyendas no colisionen con los bordes de la tarjeta.
- **Paleta de colores:** Asigna colores coordinados con la paleta de la aplicación en la prop `colors`, evitando combinaciones saturadas por defecto.

---

## 5. Modularidad y Buenas Prácticas de Código
- **Un archivo, una responsabilidad:** Separa componentes en archivos individuales (`MetricsGrid.tsx`, `IncidentsTable.tsx`, `OverviewChart.tsx`).
- **Definiciones aisladas:** Todo tipo de dato o modelo de negocio va en un archivo dedicado (`types.ts`).
- **Iconografía:** Usa iconos semánticos de `@mui/icons-material` dimensionados adecuadamente (`fontSize="small"` o `"medium"`).
