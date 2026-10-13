@AGENTS.md
# Reglas de Frontend - VehiculosRC

## Entorno y Puertos
- Servidor local activo en: http://localhost:6001 (NO usar puerto 3000).

## Herramientas MCP Obligatorias
1. shadcn MCP: Úsalo para buscar e instalar componentes base (buttons, cards, badges, dialogs, tabs).
2. magicui MCP: Úsalo para efectos dinámicos (bento grids, border-beam, shimmer buttons, blur-fade).
3. context7: Consúltalo para APIs actualizadas de Next.js App Router, Tailwind v3/v4 o Motion.
4. Playwright MCP: Cada vez que termines un componente o página:
   - Abre http://localhost:6001.
   - Toma screenshot en desktop (1280px) y mobile (375px).
   - Verifica que no exista horizontal overflow ni textos ilegibles antes de entregar la tarea.

## Animaciones e Interacción Táctil (Framer Motion / motion)
- El paquete 'motion' está instalado y es OBLIGATORIO para microinteracciones:
  1. Botones y Elementos Clicables:
     * Siempre envolver o aplicar 'whileTap={{ scale: 0.97 }}' y 'whileHover={{ scale: 1.01 }}'.
     * Usar transiciones con física de resorte: 'transition={{ type: "spring", stiffness: 400, damping: 25 }}'.
  2. Tarjetas y Paneles (Stagger):
     * Las tarjetas de KPIs y listas deben usar contenedores con variantes animadas: entrada escalonada suave (opacity: 0 -> 1, y: 10 -> 0 con staggerChildren: 0.06).
  3. Navegación y Filtros Activos:
     * Utilizar 'layoutId="active-indicator"' de Motion para que el selector activo (pestañas, filtros de turno o items de sidebar) se deslice de forma continua.
  4. Modales y Vistas Dinámicas:
     * Envolver cambios de vista y diálogos con 'AnimatePresence mode="wait"' para evitar parpadeos y transicionar con fade + slide tenue.

## Arquitectura de Layout, Jerarquía y Buenas Prácticas de UX

1. Fuente Única de Verdad para Sesión (No Duplicidad):
   - ESTRICTAMENTE PROHIBIDO duplicar el perfil de usuario o el botón de 'Cerrar Sesión'.
   - Si la información del usuario (avatar, nombre, rol, logout) ya está ubicada en la cabecera superior (Topbar/Header), el footer de la Sidebar debe mantenerse minimalista (solo versión del sistema, icono sutil o totalmente limpio). Nunca colocar dos tarjetas de usuario en la misma pantalla.

2. Separación Estricta entre Navegación y Acciones (Sidebar Hygiene):
   - La Sidebar es EXCLUSIVAMENTE para navegación de rutas jerárquicas (páginas y secciones).
   - Prohibido insertar bloques de botones de acción masivos o llamativos (como "Captura Rápida", botones de colores "+ Ambulancia / + Grúa") en la barra lateral.
   - Las acciones primarias de creación (ej. "Nueva Asistencia") deben ubicarse en la cabecera de la vista correspondiente o como un único botón sobrio en el Topbar, nunca fragmentando la navegación lateral.

3. Prohibición de Elementos Huérfanos y Bloques Inventados:
   - No crear tarjetas, accesos directos o widgets que no hayan sido pedidos de forma explícita.
   - Mantener el SidebarMenu con ítems consistentes en estilo: solo iconos monocromáticos y texto alineado, sin cambiar alturas ni insertar botones sólidos entre los enlaces.
   - En el Topbar: agrupar la navegación contextual (Breadcrumbs) a la izquierda y utilidades (Actualizar, ThemeToggle, Perfil) compactas a la derecha, sin sobrecargar con información redundante.

