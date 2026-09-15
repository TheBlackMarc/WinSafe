"""

Requisitos:
    - Windows 10/11
    - Python 3.8+ (Tkinter viene incluido en la instalación estándar)
    - Ejecutar como Administrador (el programa se re-lanza pidiendo
      elevación si hace falta)

Cómo abrirlo en Visual Studio (o VS Code):
    1. Abre Visual Studio / VS Code.
    2. Abre este archivo o la carpeta que lo contiene.
    3. Selecciona un intérprete de Python instalado.
    4. Ejecuta con F5 o el botón "Run".

"""

import ctypes
import datetime
import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

# ----------------------------------------------------------------------
# Nombre del ícono de la app (debe estar en la misma carpeta que este
# archivo, y en la misma carpeta que compilar_exe.bat)
# ----------------------------------------------------------------------

ICONO_ARCHIVO = "icono.ico"


def ruta_recurso(nombre):
    """Devuelve la ruta a un recurso, funcionando tanto si se corre el
    .py directamente como si ya está empaquetado en un .exe con
    PyInstaller (que extrae los datos extra en sys._MEIPASS)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, nombre)


# ----------------------------------------------------------------------
# Paleta de colores - tema oscuro moderno
# ----------------------------------------------------------------------

COLOR_FONDO = "#14141f"        # fondo general de la ventana
COLOR_TARJETA = "#1c1c2b"      # fondo de las "tarjetas"
COLOR_TARJETA_BORDE = "#2a2a3d"
COLOR_TEXTO = "#eaeaf2"
COLOR_TEXTO_SUAVE = "#9a9ab0"
COLOR_ACENTO = "#7c5cff"       # violeta - color principal
COLOR_ACENTO_HOVER = "#9276ff"
COLOR_ACENTO_2 = "#22d3c5"     # turquesa - color secundario (éxito/ok)
COLOR_PELIGRO = "#ff6b81"      # para "Detener"
COLOR_PELIGRO_HOVER = "#ff8a9b"
COLOR_BOTON_SUAVE = "#26263a"
COLOR_BOTON_SUAVE_HOVER = "#31314a"
COLOR_CONSOLA_FONDO = "#0f0f18"
COLOR_CONSOLA_TEXTO = "#c9c9ff"

FUENTE_BASE = ("Segoe UI", 10)
FUENTE_TITULO = ("Segoe UI Semibold", 16)
FUENTE_SUBTITULO = ("Segoe UI", 9)
FUENTE_CONSOLA = ("Cascadia Code", 9)

# ----------------------------------------------------------------------
# Elevación de permisos (equivalente a "net session" del .bat)
# ----------------------------------------------------------------------


def es_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def relanzar_como_admin():
    """Vuelve a lanzar este mismo script pidiendo elevación (UAC)."""
    script = os.path.abspath(sys.argv[0])
    params = " ".join([f'"{script}"'] + sys.argv[1:])
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )


# ----------------------------------------------------------------------
# Carpeta de logs (igual que el .bat: C:\MaintenanceLogs)
# ----------------------------------------------------------------------

LOGDIR = os.path.join(os.environ.get("SystemDrive", "C:") + os.sep, "MaintenanceLogs")
SAGEFLAG = os.path.join(LOGDIR, "cleanmgr_configurado.flag")


# ----------------------------------------------------------------------
# Ejecución "silenciosa" de subprocesos: evita que aparezcan ventanas
# de CMD / PowerShell parpadeando en pantalla mientras corre cada paso.
# ----------------------------------------------------------------------

if os.name == "nt":
    _CREATIONFLAGS = subprocess.CREATE_NO_WINDOW
    _STARTUPINFO = subprocess.STARTUPINFO()
    _STARTUPINFO.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    _STARTUPINFO.wShowWindow = subprocess.SW_HIDE
else:
    _CREATIONFLAGS = 0
    _STARTUPINFO = None


def _kwargs_silenciosos():
    """Argumentos extra para que subprocess no abra ventana visible."""
    return {
        "creationflags": _CREATIONFLAGS,
        "startupinfo": _STARTUPINFO,
    }


def preparar_log() -> str:
    os.makedirs(LOGDIR, exist_ok=True)
    marca = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    ruta = os.path.join(LOGDIR, f"Mantenimiento_{marca}.log")
    with open(ruta, "w", encoding="utf-8", errors="ignore") as f:
        f.write("=" * 60 + "\n")
        f.write("MANTENIMIENTO DE WINDOWS (interfaz gráfica)\n")
        f.write(f"Inicio: {datetime.datetime.now()}\n")
        f.write("=" * 60 + "\n")
    return ruta


def limpiar_temp_usuario(log):
    log("--- Limpiando TEMP del usuario ---")
    temp = os.environ.get("TEMP", "")
    if temp and os.path.isdir(temp):
        for nombre in os.listdir(temp):
            ruta = os.path.join(temp, nombre)
            try:
                if os.path.isdir(ruta):
                    subprocess.run(["cmd", "/c", "rd", "/s", "/q", ruta],
                                    capture_output=True, text=True,
                                    **_kwargs_silenciosos())
                else:
                    os.remove(ruta)
            except Exception as e:
                log(f"  (omitido) {nombre}: {e}")
    log("Limpieza de TEMP del usuario finalizada.")


def limpiar_temp_windows(log):
    log("--- Limpiando Windows\\Temp ---")
    wtemp = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "Temp")
    if os.path.isdir(wtemp):
        for nombre in os.listdir(wtemp):
            ruta = os.path.join(wtemp, nombre)
            try:
                if os.path.isdir(ruta):
                    subprocess.run(["cmd", "/c", "rd", "/s", "/q", ruta],
                                    capture_output=True, text=True,
                                    **_kwargs_silenciosos())
                else:
                    os.remove(ruta)
            except Exception as e:
                log(f"  (omitido) {nombre}: {e}")
    log("Limpieza de Windows\\Temp finalizada.")


def ejecutar_comando(log, comando, descripcion):
    """Ejecuta un comando externo y va mostrando su salida línea a línea."""
    log(f"--- {descripcion} ---")
    try:
        proceso = subprocess.Popen(
            comando, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, shell=isinstance(comando, str),
            **_kwargs_silenciosos(),
        )
        for linea in proceso.stdout:
            log(linea.rstrip())
        proceso.wait()
        log(f"{descripcion} -> código de salida {proceso.returncode}")
    except FileNotFoundError:
        log(f"No se encontró el comando para: {descripcion}")
    except Exception as e:
        log(f"Error ejecutando {descripcion}: {e}")


def espacio_en_disco(log):
    comando = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        "Get-Volume -DriveLetter C | Select-Object DriveLetter,"
        "FileSystemLabel,@{N='SizeGB';E={[math]::Round($_.Size/1GB,2)}},"
        "@{N='FreeGB';E={[math]::Round($_.SizeRemaining/1GB,2)}} | Format-List"
    ]
    ejecutar_comando(log, comando, "Espacio en disco (C:)")


def limpieza_disco_cleanmgr(log):
    """CleanMgr silencioso: configura una vez (sageset) y luego usa sagerun."""
    os.makedirs(LOGDIR, exist_ok=True)
    if not os.path.exists(SAGEFLAG):
        log("Primera vez: se abrirá una ventana para elegir qué categorías limpiar.")
        log("Esa elección queda guardada; las próximas veces será automática.")
        ejecutar_comando(log, ["cleanmgr", "/sageset:1"], "Configuración inicial CleanMgr")
        try:
            with open(SAGEFLAG, "w", encoding="utf-8") as f:
                f.write("configurado\n")
        except Exception as e:
            log(f"No se pudo guardar el marcador de configuración: {e}")
    ejecutar_comando(log, ["cleanmgr", "/sagerun:1"], "CleanMgr (silencioso)")


PASOS = [
    ("Espacio en disco (C:)", espacio_en_disco),
    ("Limpiar TEMP del usuario", limpiar_temp_usuario),
    ("Limpiar TEMP de Windows", limpiar_temp_windows),
    ("DISM: limpieza de componentes", lambda log: ejecutar_comando(
        log, ["DISM", "/Online", "/Cleanup-Image", "/StartComponentCleanup"],
        "DISM StartComponentCleanup")),
    ("DISM: reparar imagen", lambda log: ejecutar_comando(
        log, ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
        "DISM RestoreHealth")),
    ("SFC: archivos del sistema", lambda log: ejecutar_comando(
        log, ["sfc", "/scannow"], "SFC Scannow")),
    ("Vaciar caché DNS", lambda log: ejecutar_comando(
        log, ["ipconfig", "/flushdns"], "Flush DNS")),
    ("Vaciar Papelera", lambda log: ejecutar_comando(
        log, ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
              "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
        "Vaciar papelera")),
    ("Optimizar unidad C:", lambda log: ejecutar_comando(
        log, ["defrag", "C:", "/O", "/U", "/V"], "Optimizar unidad C:")),
    ("Limpieza de disco (CleanMgr)", limpieza_disco_cleanmgr),
]




class BotonRedondeado(tk.Canvas):
    def __init__(self, parent, texto, comando=None, ancho=200, alto=40,
                 color=COLOR_ACENTO, color_hover=COLOR_ACENTO_HOVER,
                 color_texto="#ffffff", radio=14, fuente=("Segoe UI", 10, "bold")):
        super().__init__(parent, width=ancho, height=alto,
                          bg=parent["bg"] if isinstance(parent, (tk.Frame, tk.Canvas))
                          else COLOR_FONDO,
                          highlightthickness=0, cursor="hand2")
        self.comando = comando
        self.color = color
        self.color_hover = color_hover
        self.color_texto = color_texto
        self.radio = radio
        self.ancho = ancho
        self.alto = alto
        self.habilitado = True

        self._dibujar(color)
        self.texto_id = self.create_text(
            ancho / 2, alto / 2, text=texto, fill=color_texto, font=fuente)

        self.bind("<Enter>", self._al_entrar)
        self.bind("<Leave>", self._al_salir)
        self.bind("<Button-1>", self._al_click)

    def _redondeado_puntos(self, x1, y1, x2, y2, r):
        return [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]

    def _dibujar(self, color):
        self.delete("fondo")
        puntos = self._redondeado_puntos(1, 1, self.ancho - 1, self.alto - 1, self.radio)
        self.create_polygon(puntos, smooth=True, fill=color, outline=color, tags="fondo")
        self.tag_lower("fondo")

    def _al_entrar(self, _e):
        if self.habilitado:
            self._dibujar(self.color_hover)

    def _al_salir(self, _e):
        if self.habilitado:
            self._dibujar(self.color)

    def _al_click(self, _e):
        if self.habilitado and self.comando:
            self.comando()

    def set_habilitado(self, habilitado: bool):
        self.habilitado = habilitado
        if habilitado:
            self._dibujar(self.color)
            self.itemconfig(self.texto_id, fill=self.color_texto)
            self.configure(cursor="hand2")
        else:
            self._dibujar(COLOR_BOTON_SUAVE)
            self.itemconfig(self.texto_id, fill=COLOR_TEXTO_SUAVE)
            self.configure(cursor="arrow")


class BotonPaso(tk.Button):
    """Botón plano (rectangular) para los pasos individuales, con hover."""

    def __init__(self, parent, texto, comando):
        super().__init__(
            parent, text=texto, command=comando, anchor="w",
            bg=COLOR_BOTON_SUAVE, fg=COLOR_TEXTO, activebackground=COLOR_BOTON_SUAVE_HOVER,
            activeforeground=COLOR_TEXTO, bd=0, relief="flat", padx=14, pady=10,
            font=FUENTE_BASE, cursor="hand2", highlightthickness=0,
        )
        self.bind("<Enter>", lambda e: self.configure(bg=COLOR_BOTON_SUAVE_HOVER))
        self.bind("<Leave>", lambda e: self.configure(bg=COLOR_BOTON_SUAVE))


def tarjeta(parent, **kwargs):
    """Crea un Frame con aspecto de 'tarjeta' plana moderna."""
    marco = tk.Frame(parent, bg=COLOR_TARJETA, highlightthickness=1,
                      highlightbackground=COLOR_TARJETA_BORDE, **kwargs)
    return marco


# ----------------------------------------------------------------------
# Interfaz gráfica principal
# ----------------------------------------------------------------------


class AppMantenimiento(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WinSafe por MarcTech")
        self.geometry("820x680")
        self.minsize(700, 560)
        self.configure(bg=COLOR_FONDO)

        try:
            self.iconbitmap(ruta_recurso(ICONO_ARCHIVO))
        except (tk.TclError, FileNotFoundError):
            pass  # si el .ico no está presente, sigue con el ícono por defecto

        # Opacidad inicial de la ventana (efecto vidrio). En Windows
        # esto sí aplica sobre la ventana completa vía -alpha.
        self._alpha_actual = 0.97
        try:
            self.attributes("-alpha", self._alpha_actual)
        except tk.TclError:
            pass

        self.ruta_log = None
        self.hilo_activo = None
        self._cancelar = False

        self._construir_widgets()
        self.after(150, self._verificar_admin)

    # -- construcción visual ------------------------------------------------
    def _construir_widgets(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        estilo.configure(
            "Moderna.Horizontal.TProgressbar",
            troughcolor=COLOR_TARJETA, background=COLOR_ACENTO_2,
            bordercolor=COLOR_TARJETA, lightcolor=COLOR_ACENTO_2,
            darkcolor=COLOR_ACENTO_2, thickness=10,
        )
        estilo.configure(
            "Moderna.Horizontal.TScale",
            background=COLOR_FONDO, troughcolor=COLOR_TARJETA,
        )

        contenedor = tk.Frame(self, bg=COLOR_FONDO)
        contenedor.pack(fill="both", expand=True, padx=18, pady=16)

        # ---------------- Cabecera ----------------
        cabecera = tk.Frame(contenedor, bg=COLOR_FONDO)
        cabecera.pack(fill="x", pady=(0, 14))

        bloque_titulo = tk.Frame(cabecera, bg=COLOR_FONDO)
        bloque_titulo.pack(side="left")
        tk.Label(bloque_titulo, text="Mantenimiento Seguro de Windows",
                 font=FUENTE_TITULO, bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(anchor="w")
        tk.Label(bloque_titulo, text="Limpieza, reparación y optimización del sistema",
                 font=FUENTE_SUBTITULO, bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE).pack(anchor="w")

        bloque_derecha = tk.Frame(cabecera, bg=COLOR_FONDO)
        bloque_derecha.pack(side="right")

        fila_admin = tk.Frame(bloque_derecha, bg=COLOR_FONDO)
        fila_admin.pack(anchor="e")
        self.lbl_admin = tk.Label(fila_admin, text="Comprobando permisos...",
                                   font=FUENTE_SUBTITULO, bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE)
        self.lbl_admin.pack(side="left")

        self.btn_acerca_de = tk.Button(
            fila_admin, text="Acerca de", command=self.mostrar_acerca_de,
            bg=COLOR_BOTON_SUAVE, fg=COLOR_TEXTO, activebackground=COLOR_BOTON_SUAVE_HOVER,
            activeforeground=COLOR_TEXTO, bd=0, relief="flat", padx=10, pady=2,
            font=("Segoe UI", 8), cursor="hand2", highlightthickness=0)
        self.btn_acerca_de.pack(side="left", padx=(10, 0))
        self.btn_acerca_de.bind("<Enter>", lambda e: self.btn_acerca_de.configure(bg=COLOR_BOTON_SUAVE_HOVER))
        self.btn_acerca_de.bind("<Leave>", lambda e: self.btn_acerca_de.configure(bg=COLOR_BOTON_SUAVE))

        bloque_opacidad = tk.Frame(bloque_derecha, bg=COLOR_FONDO)
        bloque_opacidad.pack(anchor="e", pady=(6, 0))
        tk.Label(bloque_opacidad, text="Opacidad", font=("Segoe UI", 8),
                 bg=COLOR_FONDO, fg=COLOR_TEXTO_SUAVE).pack(side="left", padx=(0, 6))
        self.control_opacidad = ttk.Scale(
            bloque_opacidad, from_=0.55, to=1.0, orient="horizontal", length=110,
            value=self._alpha_actual, style="Moderna.Horizontal.TScale",
            command=self._cambiar_opacidad)
        self.control_opacidad.pack(side="left")

        # ---------------- Tarjeta: acciones principales ----------------
        tarjeta_acciones = tarjeta(contenedor)
        tarjeta_acciones.pack(fill="x", pady=(0, 14), ipady=10)

        fila_acciones = tk.Frame(tarjeta_acciones, bg=COLOR_TARJETA)
        fila_acciones.pack(fill="x", padx=14, pady=10)

        self.btn_ejecutar_todo = BotonRedondeado(
            fila_acciones, "▶  Ejecutar mantenimiento completo",
            comando=self.ejecutar_todo, ancho=300, alto=42,
            color=COLOR_ACENTO, color_hover=COLOR_ACENTO_HOVER)
        self.btn_ejecutar_todo.pack(side="left")

        self.btn_cancelar = BotonRedondeado(
            fila_acciones, "Detener", comando=self.solicitar_cancelacion,
            ancho=110, alto=42, color=COLOR_PELIGRO, color_hover=COLOR_PELIGRO_HOVER)
        self.btn_cancelar.pack(side="left", padx=(10, 0))
        self.btn_cancelar.set_habilitado(False)

        marco_progreso = tk.Frame(tarjeta_acciones, bg=COLOR_TARJETA)
        marco_progreso.pack(fill="x", padx=14, pady=(0, 10))#f
        self.progreso = ttk.Progressbar(#p
            marco_progreso, mode="determinate", maximum=len(PASOS),#e
            style="Moderna.Horizontal.TProgressbar")#r
        self.progreso.pack(fill="x")#e

        self.lbl_estado = tk.Label(tarjeta_acciones, text="Listo.", font=FUENTE_SUBTITULO,#z
                                    bg=COLOR_TARJETA, fg=COLOR_TEXTO_SUAVE)
        self.lbl_estado.pack(anchor="w", padx=14, pady=(0, 4))

        # ---------------- Tarjeta: pasos individuales ----------------
        tarjeta_pasos = tarjeta(contenedor)
        tarjeta_pasos.pack(fill="x", pady=(0, 14))

        tk.Label(tarjeta_pasos, text="Pasos individuales", font=("Segoe UI", 10, "bold"),
                 bg=COLOR_TARJETA, fg=COLOR_TEXTO).pack(anchor="w", padx=14, pady=(12, 6))

        marco_pasos = tk.Frame(tarjeta_pasos, bg=COLOR_TARJETA)
        marco_pasos.pack(fill="x", padx=10, pady=(0, 12))
        marco_pasos.columnconfigure(0, weight=1)
        marco_pasos.columnconfigure(1, weight=1)

        for i, (nombre, _) in enumerate(PASOS):
            fila, columna = divmod(i, 2)
            boton = BotonPaso(marco_pasos, nombre,
                               comando=lambda idx=i: self.ejecutar_paso_individual(idx))
            boton.grid(row=fila, column=columna, sticky="ew", padx=4, pady=3)

        # ---------------- Tarjeta: consola / registro (abajo) ----------------
        tarjeta_consola = tarjeta(contenedor)
        tarjeta_consola.pack(fill="both", expand=True)

        cabecera_consola = tk.Frame(tarjeta_consola, bg=COLOR_TARJETA)
        cabecera_consola.pack(fill="x", padx=14, pady=(10, 4))
        tk.Label(cabecera_consola, text="● Consola / Registro en vivo",
                 font=("Segoe UI", 10, "bold"), bg=COLOR_TARJETA,
                 fg=COLOR_ACENTO_2).pack(side="left")

        self.texto_log = scrolledtext.ScrolledText(
            tarjeta_consola, bg=COLOR_CONSOLA_FONDO, fg=COLOR_CONSOLA_TEXTO,
            insertbackground=COLOR_CONSOLA_TEXTO, font=FUENTE_CONSOLA,
            wrap="word", bd=0, highlightthickness=0)
        self.texto_log.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.texto_log.configure(state="disabled")

    # -- opacidad -------------------------------------------------------------
    def _cambiar_opacidad(self, valor):
        try:
            self.attributes("-alpha", float(valor))
        except tk.TclError:
            pass

    # -- acerca de --------------------------------------------------------------
    def mostrar_acerca_de(self):
        messagebox.showinfo("Acerca de", "Programado por Facundo Pèrez")

    # -- permisos ---------------------------------------------------------------
    def _verificar_admin(self):
        if es_admin():
            self.lbl_admin.configure(text="✔  Ejecutando como administrador",
                                      fg=COLOR_ACENTO_2)
        else:
            self.lbl_admin.configure(text="⚠  Sin permisos de administrador",
                                      fg=COLOR_PELIGRO)
            respuesta = messagebox.askyesno(
                "Permisos de administrador requeridos",
                "Este programa necesita permisos de administrador para "
                "ejecutar DISM, SFC y otras tareas.\n\n"
                "¿Quieres reiniciarlo ahora con permisos de administrador?"
            )
            if respuesta:
                relanzar_como_admin()
                self.destroy()
                sys.exit(0)

    # -- utilidades de registro ----------------------------------------------
    def escribir_log(self, texto: str):
        def _actualizar():
            self.texto_log.configure(state="normal")
            self.texto_log.insert("end", texto + "\n")
            self.texto_log.see("end")
            self.texto_log.configure(state="disabled")
        self.after(0, _actualizar)

        if self.ruta_log:
            try:
                with open(self.ruta_log, "a", encoding="utf-8", errors="ignore") as f:
                    f.write(texto + "\n")
            except Exception:
                pass

    # -- ejecución -------------------------------------------------------------
    def _bloquear_botones(self, bloquear: bool):
        self.btn_ejecutar_todo.set_habilitado(not bloquear)
        self.btn_cancelar.set_habilitado(bloquear)

    def ejecutar_paso_individual(self, indice: int):
        if self.hilo_activo and self.hilo_activo.is_alive():
            messagebox.showinfo("En curso", "Ya hay una tarea en ejecución.")
            return
        nombre, funcion = PASOS[indice]

        def tarea():
            self.ruta_log = self.ruta_log or preparar_log()
            self._bloquear_botones(True)
            self.lbl_estado.configure(text=f"Ejecutando: {nombre}...")
            self.escribir_log(f"\n>>> {nombre}")
            try:
                funcion(self.escribir_log)
            except Exception as e:
                self.escribir_log(f"Error: {e}")
            self.lbl_estado.configure(text="Listo.")
            self._bloquear_botones(False)

        self.hilo_activo = threading.Thread(target=tarea, daemon=True)
        self.hilo_activo.start()

    def solicitar_cancelacion(self):
        self._cancelar = True
        self.lbl_estado.configure(text="Deteniendo tras el paso actual...")

    def ejecutar_todo(self):
        if self.hilo_activo and self.hilo_activo.is_alive():
            return
        self._cancelar = False

        def tarea():
            self.ruta_log = preparar_log()
            self._bloquear_botones(True)
            self.progreso["value"] = 0
            self.escribir_log(f"Registro: {self.ruta_log}")

            for i, (nombre, funcion) in enumerate(PASOS, start=1):
                if self._cancelar:
                    self.escribir_log("\nMantenimiento detenido por el usuario.")
                    break
                self.lbl_estado.configure(text=f"[{i}/{len(PASOS)}] {nombre}")
                self.escribir_log(f"\n>>> [{i}/{len(PASOS)}] {nombre}")
                try:
                    funcion(self.escribir_log)
                except Exception as e:
                    self.escribir_log(f"Error: {e}")
                self.progreso["value"] = i

            self.escribir_log("\nMantenimiento finalizado.")
            self.escribir_log(
                "Recomendación: reinicia Windows para completar cualquier "
                "reparación pendiente.")
            self.lbl_estado.configure(text="Mantenimiento finalizado.")
            self._bloquear_botones(False)

        self.hilo_activo = threading.Thread(target=tarea, daemon=True)
        self.hilo_activo.start()


if __name__ == "__main__":
    if os.name != "nt":
        print("Este programa está diseñado para ejecutarse en Windows.")
        sys.exit(1)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "MarcTech.WinSafe")
    except Exception:
        pass
    app = AppMantenimiento()
    app.mainloop()
