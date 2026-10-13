import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { UserRole } from "@/types/auth";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Ignorar peticiones a recursos estáticos de Next.js, imágenes y favicons
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".") // Archivos estáticos como .ico, .png, etc.
  ) {
    return NextResponse.next();
  }

  // Extraer cookies de autenticación
  const token = request.cookies.get("token_rc")?.value;
  const userCookie = request.cookies.get("user_rc")?.value;

  let userRole: UserRole | null = null;
  if (userCookie) {
    try {
      const parsed = JSON.parse(decodeURIComponent(userCookie));
      userRole = parsed?.rol as UserRole;
    } catch {
      try {
        const parsed = JSON.parse(userCookie);
        userRole = parsed?.rol as UserRole;
      } catch {
        userRole = null;
      }
    }
  }

  const isAuthenticated = !!token;
  const isLoginPage = pathname === "/";

  // 1. Redirección de usuario autenticado que intenta entrar a la página de Login
  if (isAuthenticated && isLoginPage) {
    const dashboardUrl = new URL("/dashboard", request.url);
    return NextResponse.redirect(dashboardUrl);
  }

  // 2. Redirección de usuario NO autenticado que intenta entrar a rutas protegidas
  const isProtectedRoute =
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/operaciones") ||
    pathname.startsWith("/configuracion");

  if (!isAuthenticated && isProtectedRoute) {
    const loginUrl = new URL("/", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 3. Reglas RBAC para VISUALIZADOR (Bloquear creación/edición en /operaciones/nuevo/*)
  if (
    isAuthenticated &&
    pathname.startsWith("/operaciones/nuevo") &&
    userRole === "VISUALIZADOR"
  ) {
    const unauthorizedUrl = new URL("/dashboard", request.url);
    unauthorizedUrl.searchParams.set("error", "unauthorized_role_visualizador");
    return NextResponse.redirect(unauthorizedUrl);
  }

  // 4. Reglas RBAC para Configuración (Solo ADMIN)
  if (
    isAuthenticated &&
    pathname.startsWith("/configuracion") &&
    userRole !== "ADMIN"
  ) {
    const unauthorizedUrl = new URL("/dashboard", request.url);
    unauthorizedUrl.searchParams.set("error", "unauthorized_role_admin_only");
    return NextResponse.redirect(unauthorizedUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/dashboard",
    "/dashboard/:path*",
    "/operaciones/:path*",
    "/configuracion/:path*",
  ],
};
