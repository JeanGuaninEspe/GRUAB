"use client";

import * as React from "react";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock,
  Eye,
  EyeOff,
  KeyRound,
  Layers,
  Loader2,
  Lock,
  Mail,
  ShieldCheck,
  TrendingUp,
  UserCheck,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { BorderBeam } from "@/components/ui/border-beam";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { DotPattern } from "@/components/ui/dot-pattern";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme-toggle";
import { useAuth } from "@/context/auth-context";
import { toast } from "sonner";
import { motion } from "motion/react";

const MONTHLY_STATS = [
  { month: "May", gruas: 240, amb: 110 },
  { month: "Jun", gruas: 285, amb: 130 },
  { month: "Jul", gruas: 310, amb: 145 },
  { month: "Ago", gruas: 295, amb: 135 },
  { month: "Sep", gruas: 340, amb: 160 },
  { month: "Oct", gruas: 380, amb: 180 },
];

interface LoginViewProps {
  onLoginSuccess?: () => void;
}

export function LoginView({ onLoginSuccess }: LoginViewProps) {
  const { login } = useAuth();
  const [email, setEmail] = React.useState("admin@concesion.com");
  const [password, setPassword] = React.useState("admin2026");
  const [showPassword, setShowPassword] = React.useState(false);
  const [rememberDevice, setRememberDevice] = React.useState(true);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isSuccess, setIsSuccess] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Por favor completa tu correo y contraseña");
      return;
    }

    setIsSubmitting(true);
    try {
      await login({ email, password }, rememberDevice);
      setIsSuccess(true);
      if (onLoginSuccess) {
        onLoginSuccess();
      }
    } catch (err: any) {
      toast.error(err.message || "Credenciales incorrectas o fallo de conexión");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickLogin = async (quickEmail: string, quickPass: string) => {
    setEmail(quickEmail);
    setPassword(quickPass);
    setIsSubmitting(true);
    try {
      await login({ email: quickEmail, password: quickPass }, rememberDevice);
      setIsSuccess(true);
      if (onLoginSuccess) {
        onLoginSuccess();
      }
    } catch (err: any) {
      toast.error(err.message || "Error al iniciar sesión");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col lg:flex-row bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 transition-colors duration-200 relative">
      {/* Botón Flotante para Alternar Tema Claro / Oscuro */}
      <div className="fixed top-5 right-5 z-50">
        <ThemeToggle />
      </div>

      {/* Columna Izquierda: Formulario SaaS Split-Screen */}
      <div className="w-full lg:w-[45%] xl:w-[40%] min-h-screen flex flex-col justify-between p-6 sm:p-10 lg:p-12 xl:p-16 border-r border-zinc-200 dark:border-zinc-900 bg-white dark:bg-zinc-950 z-10">
        {/* Brand Header */}
        <div className="flex items-center gap-2.5">
          <div className="flex size-7 items-center justify-center rounded-md bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-200">
            <Layers className="size-4 text-zinc-800 dark:text-zinc-300" />
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              VehículosRC
            </span>
            <span className="text-zinc-400 dark:text-zinc-600">/</span>
            <span className="text-zinc-600 dark:text-zinc-400">
              Control Operativo y RBAC
            </span>
          </div>
        </div>

        {/* Form Container */}
        <div className="w-full max-w-sm mx-auto my-auto py-8 sm:py-12">
          <div className="mb-6">
            <h1 className="text-2xl sm:text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
              Iniciar sesión
            </h1>
            <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
              Ingresa con tus credenciales seguras para acceder al panel de auditoría, bitácoras y gestión vehicular.
            </p>
          </div>

          {isSuccess ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/50 dark:bg-emerald-950/20 p-6 text-center space-y-3"
            >
              <div className="flex justify-center">
                <CheckCircle2 className="size-10 text-emerald-600 dark:text-emerald-400 animate-bounce" />
              </div>
              <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">
                Acceso concedido
              </h3>
              <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Cargando tu perfil operativo y permisos asignados...
              </p>
            </motion.div>
          ) : (
            <div className="space-y-5">
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Campo: Correo electrónico */}
                <div className="space-y-1.5">
                  <Label htmlFor="email" className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                    Correo electrónico
                  </Label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400 dark:text-zinc-500">
                      <Mail className="size-4" />
                    </div>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="admin@concesion.com"
                      required
                      className="h-11 pl-9 pr-3 text-sm bg-white dark:bg-zinc-900/50 border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus-visible:ring-1 focus-visible:ring-zinc-900 dark:focus-visible:ring-zinc-400 focus-visible:border-zinc-900 dark:focus-visible:border-zinc-400 transition-colors rounded-lg"
                    />
                  </div>
                </div>

                {/* Campo: Contraseña */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password" className="text-xs font-medium text-zinc-700 dark:text-zinc-300">
                      Contraseña
                    </Label>
                    <a
                      href="#recuperar"
                      onClick={(e) => {
                        e.preventDefault();
                        toast.info("Comuníquese con el Administrador del Sistema para restablecer su clave.");
                      }}
                      className="text-xs text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors"
                    >
                      ¿Olvidaste tu contraseña?
                    </a>
                  </div>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400 dark:text-zinc-500">
                      <Lock className="size-4" />
                    </div>
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      required
                      className="h-11 pl-9 pr-10 text-sm bg-white dark:bg-zinc-900/50 border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-600 focus-visible:ring-1 focus-visible:ring-zinc-900 dark:focus-visible:ring-zinc-400 focus-visible:border-zinc-900 dark:focus-visible:border-zinc-400 transition-colors rounded-lg"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center text-zinc-400 dark:text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300 transition-colors cursor-pointer"
                      aria-label={showPassword ? "Ocultar contraseña" : "Ver contraseña"}
                    >
                      {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </button>
                  </div>
                </div>

                {/* Checkbox: Recordar este dispositivo */}
                <div className="flex items-center space-x-2 pt-1 pb-1">
                  <Checkbox
                    id="remember-device"
                    checked={rememberDevice}
                    onCheckedChange={(checked) => setRememberDevice(Boolean(checked))}
                    className="border-zinc-300 dark:border-zinc-700 data-checked:border-zinc-900 dark:data-checked:border-zinc-100 data-checked:bg-zinc-900 dark:data-checked:bg-zinc-100 data-checked:text-white dark:data-checked:text-zinc-950"
                  />
                  <Label
                    htmlFor="remember-device"
                    className="text-xs text-zinc-600 dark:text-zinc-400 font-normal cursor-pointer select-none"
                  >
                    Recordar este dispositivo por 30 días
                  </Label>
                </div>

                {/* Botón Submit: Ingresar al Panel */}
                <motion.div
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.98 }}
                  transition={{ type: "spring", stiffness: 400, damping: 25 }}
                >
                  <Button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full h-11 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-white dark:bg-zinc-100 dark:hover:bg-zinc-200 dark:text-zinc-950 font-medium text-sm transition-all duration-150 flex items-center justify-center gap-2 shadow-sm cursor-pointer disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="size-4 animate-spin" />
                        <span>Ingresando al sistema...</span>
                      </>
                    ) : (
                      <>
                        <span>Ingresar al Panel</span>
                        <ArrowRight className="size-4" />
                      </>
                    )}
                  </Button>
                </motion.div>
              </form>

              {/* Botones Discretos de Acceso Rápido para Pruebas RBAC */}
              <div className="pt-3 border-t border-zinc-100 dark:border-zinc-800/80 space-y-2">
                <div className="flex items-center justify-between text-[11px] text-zinc-500 dark:text-zinc-400">
                  <div className="flex items-center gap-1">
                    <KeyRound className="size-3 text-zinc-400" />
                    <span>Cuentas de prueba rápida (RBAC):</span>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-1.5">
                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                    disabled={isSubmitting}
                    onClick={() => handleQuickLogin("admin@concesion.com", "admin2026")}
                    className="px-2 py-1.5 rounded-lg border border-purple-200/80 dark:border-purple-800/60 bg-purple-50/50 dark:bg-purple-950/20 text-purple-700 dark:text-purple-300 text-[11px] font-medium text-center hover:bg-purple-100/70 dark:hover:bg-purple-900/40 transition-colors cursor-pointer flex flex-col items-center gap-0.5"
                  >
                    <span className="font-semibold">ADMIN</span>
                    <span className="text-[9px] text-purple-600/80 dark:text-purple-400">Acceso Total</span>
                  </motion.button>

                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                    disabled={isSubmitting}
                    onClick={() => handleQuickLogin("operaciones@concesion.com", "jefe2026")}
                    className="px-2 py-1.5 rounded-lg border border-blue-200/80 dark:border-blue-800/60 bg-blue-50/50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300 text-[11px] font-medium text-center hover:bg-blue-100/70 dark:hover:bg-blue-900/40 transition-colors cursor-pointer flex flex-col items-center gap-0.5"
                  >
                    <span className="font-semibold">JEFE OPER.</span>
                    <span className="text-[9px] text-blue-600/80 dark:text-blue-400">Escritura/Asist.</span>
                  </motion.button>

                  <motion.button
                    type="button"
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.97 }}
                    disabled={isSubmitting}
                    onClick={() => handleQuickLogin("auditoria@concesion.com", "auditor2026")}
                    className="px-2 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300 text-[11px] font-medium text-center hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer flex flex-col items-center gap-0.5"
                  >
                    <span className="font-semibold">VISUALIZADOR</span>
                    <span className="text-[9px] text-zinc-500">Solo Lectura</span>
                  </motion.button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Discreto */}
        <div className="pt-4 border-t border-zinc-100 dark:border-zinc-900 text-xs text-zinc-500 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="size-3.5 text-zinc-400 dark:text-zinc-400" />
            <span>Acceso seguro con cifrado JWT & TLS 1.3</span>
          </div>
          <a
            href="#soporte"
            onClick={(e) => {
              e.preventDefault();
              toast.info("Mesa de ayuda técnica: soporte@vehiculosrc.com");
            }}
            className="text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-300 transition-colors"
          >
            Soporte de Sistemas
          </a>
        </div>
      </div>

      {/* Columna Derecha: Dashboard SaaS Preview */}
      <div className="hidden lg:flex flex-1 relative items-center justify-center p-8 xl:p-14 bg-zinc-50/50 dark:bg-gradient-to-br dark:from-zinc-950 dark:via-[#0c0e14] dark:to-zinc-950 border-l border-zinc-200/80 dark:border-zinc-900 overflow-hidden">
        <DotPattern
          width={24}
          height={24}
          cx={1}
          cy={1}
          cr={1}
          className="text-zinc-300/80 dark:text-zinc-800/80 [mask-image:radial-gradient(ellipse_at_center,white,transparent_75%)] opacity-70 pointer-events-none"
        />

        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[460px] h-[320px] bg-blue-500/5 rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute bottom-10 right-10 w-[380px] h-[240px] bg-indigo-500/5 rounded-full blur-[120px] pointer-events-none" />

        <div className="relative w-full max-w-lg rounded-2xl border border-zinc-200/80 dark:border-zinc-800/90 bg-white dark:bg-zinc-900/60 backdrop-blur-xl p-6 sm:p-7 shadow-sm dark:shadow-2xl dark:shadow-black/80">
          <BorderBeam
            size={80}
            duration={9}
            delay={0}
            colorFrom="#0284c7"
            colorTo="#6366f1"
            borderWidth={1}
          />

          <div className="flex items-start justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-5">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <BarChart3 className="size-4 text-blue-600 dark:text-blue-400" />
                <h2 className="text-base font-semibold text-zinc-900 dark:text-zinc-100 tracking-tight">
                  Resumen Operativo Mensual
                </h2>
              </div>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                Auditoría consolidada de asistencias viales y reportes de flota
              </p>
            </div>
            <Badge
              variant="outline"
              className="border-zinc-200 dark:border-zinc-700/60 bg-zinc-100/80 dark:bg-zinc-800/60 text-zinc-700 dark:text-zinc-300 text-[11px] font-normal px-2.5 py-0.5"
            >
              Histórico consolidado
            </Badge>
          </div>

          <div className="grid grid-cols-2 gap-4 py-5 border-b border-zinc-100 dark:border-zinc-800/80">
            <div className="space-y-1.5 p-3.5 rounded-xl bg-zinc-50/80 dark:bg-zinc-950/50 border border-zinc-200/80 dark:border-zinc-800/60">
              <span className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">Asistencias Finalizadas</span>
              <div className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 font-sans">
                2,418
              </div>
              <div className="flex items-center gap-1 text-[11px] font-medium text-emerald-700 dark:text-emerald-400">
                <TrendingUp className="size-3" />
                <span>+8.4% vs mes anterior</span>
              </div>
            </div>

            <div className="space-y-1.5 p-3.5 rounded-xl bg-zinc-50/80 dark:bg-zinc-950/50 border border-zinc-200/80 dark:border-zinc-800/60">
              <span className="text-xs text-zinc-500 dark:text-zinc-400 font-medium">Tiempo Promedio en Sitio</span>
              <div className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100 font-sans">
                18 min
              </div>
              <div className="flex items-center gap-1 text-[11px] font-medium text-blue-700 dark:text-blue-400">
                <Clock className="size-3" />
                <span>-2.1 min optimización</span>
              </div>
            </div>
          </div>

          <div className="pt-5 space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium text-zinc-800 dark:text-zinc-300">
                Distribución Histórica (Grúas vs Ambulancias)
              </span>
              <span className="text-zinc-500 font-mono text-[11px]">Últimos 6 meses</span>
            </div>

            <div className="h-28 flex items-end justify-between gap-3 pt-4 px-2 pb-1 bg-zinc-50 dark:bg-zinc-950/40 rounded-xl border border-zinc-200/60 dark:border-zinc-800/40">
              {MONTHLY_STATS.map((item) => {
                const gruasHeight = (item.gruas / 600) * 100;
                const ambHeight = (item.amb / 600) * 100;

                return (
                  <div key={item.month} className="flex-1 flex flex-col items-center h-full justify-end gap-1.5 group">
                    <div className="w-full max-w-[28px] flex flex-col gap-0.5 justify-end h-full">
                      <div
                        style={{ height: `${ambHeight}%` }}
                        className="w-full bg-emerald-500 rounded-t-sm transition-all group-hover:bg-emerald-600 dark:group-hover:bg-emerald-400"
                        title={`${item.month} - Ambulancias: ${item.amb}`}
                      />
                      <div
                        style={{ height: `${gruasHeight}%` }}
                        className="w-full bg-blue-600 dark:bg-blue-500 rounded-b-sm transition-all group-hover:bg-blue-700 dark:group-hover:bg-blue-400"
                        title={`${item.month} - Grúas: ${item.gruas}`}
                      />
                    </div>
                    <span className="text-[10px] text-zinc-500 dark:text-zinc-500 font-mono group-hover:text-zinc-900 dark:group-hover:text-zinc-300">
                      {item.month}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="flex items-center justify-between pt-2 px-1 text-xs text-zinc-600 dark:text-zinc-400">
              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-blue-600 dark:bg-blue-500" />
                <span>Grúas de plataforma: <strong className="text-zinc-900 dark:text-zinc-200">1,644 (68%)</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <span className="size-2 rounded-full bg-emerald-600 dark:bg-emerald-500" />
                <span>Ambulancias: <strong className="text-zinc-900 dark:text-zinc-200">774 (32%)</strong></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
