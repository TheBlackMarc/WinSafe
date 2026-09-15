# WinSafe 🛡️

![Licencia](https://img.shields.io/badge/licencia-GPLv3-blue.svg)

**WinSafe** es una herramienta de mantenimiento para Windows con interfaz gráfica en Python. Automatiza tareas de limpieza, reparación y optimización del sistema que normalmente se hacen a mano desde la consola: temporales, DISM, SFC, DNS, papelera, desfragmentación y liberador de espacio en disco — todo desde una interfaz simple, con registro en vivo, todo sin anuncios ni pagos externos esto para no depender de apps que prometen mantenimiento a windows pero solo son anuncios con un boton de limpiar.

![Captura de WinSafe](WinSafe.png)

## ✨ Características

- **Interfaz gráfica simple**, hecha con Python y Tkinter (sin dependencias externas).
- **Un botón para correr todo**, o botones individuales para ejecutar cada paso por separado.
- **Consola / registro en vivo**: muestra la salida de cada comando en tiempo real y la guarda automáticamente en `C:\MaintenanceLogs`.
- **Barra de progreso** durante el mantenimiento completo, con opción de detenerlo en cualquier momento.
- **Comprobación de permisos de administrador** al iniciar, con opción de relanzar el programa elevado (UAC).
- **No modifica el Registro** ni desactiva servicios (salvo la configuración estándar de categorías del Liberador de espacio en disco, que Windows guarda para poder ejecutarlo en modo silencioso).

### Pasos que ejecuta

| # | Paso | Comando/acción |
|---|------|-----------------|
| 1 | Espacio en disco | `Get-Volume` (PowerShell) |
| 2 | Limpiar TEMP del usuario | Borrado de `%TEMP%` |
| 3 | Limpiar TEMP de Windows | Borrado de `%SystemRoot%\Temp` |
| 4 | Limpieza de componentes | `DISM /Online /Cleanup-Image /StartComponentCleanup` |
| 5 | Reparar imagen de Windows | `DISM /Online /Cleanup-Image /RestoreHealth` |
| 6 | Comprobar archivos del sistema | `sfc /scannow` |
| 7 | Vaciar caché DNS | `ipconfig /flushdns` |
| 8 | Vaciar papelera | `Clear-RecycleBin` (PowerShell) |
| 9 | Optimizar unidad C: | `defrag C: /O /U /V` |
| 10 | Limpieza de disco | `cleanmgr` (modo silencioso con `/sagerun`) |

## 📋 Requisitos

- Windows 10 u 11.
- Python 3.8 o superior (Tkinter viene incluido en la instalación estándar desde [python.org](https://www.python.org/)).
- Permisos de administrador (el programa te los pide automáticamente si hace falta).

## 🚀 Instalación y uso

1. Cloná o descargá este repositorio.
   ```bash
   git clone https://github.com/TheBlackMarc/WinSafe.git
   cd WinSafe
   ```
2. Ejecutá el programa:
   ```bash
   python mantenimiento_gui.py
   ```
3. Si Windows no te dio permisos de administrador automáticamente, aceptá el aviso de UAC que aparece al iniciar.

### Ejecutar desde Visual Studio / VS Code

1. Abrí la carpeta del proyecto en Visual Studio o VS Code.
2. Verificá que tengas un intérprete de Python configurado (extensión "Python" en VS Code, o "Python Environments" en Visual Studio).
3. Ejecutá con `F5` o el botón "Run".

## 📂 Estructura del proyecto

```
WinSafe/
├── mantenimiento_gui.py   # Interfaz gráfica principal
├── WinSafe.png            # Captura de pantalla del programa
└── README.md
```

## ⚠️ Aviso

Este programa ejecuta herramientas nativas de Windows (DISM, SFC, defrag, cleanmgr) que pueden tardar varios minutos, especialmente `DISM /RestoreHealth` y `sfc /scannow`. No apagues el equipo mientras estén en ejecución. El registro completo de cada sesión queda guardado en `C:\MaintenanceLogs` para poder revisar qué se hizo.

## 📄 Licencia

Este proyecto está licenciado bajo la **GNU General Public License v3.0**. Podés usar, modificar y redistribuir el código, siempre que cualquier trabajo derivado se distribuya bajo la misma licencia. Ver el archivo [LICENSE](LICENSE) para el texto completo.

## 👤 Autor

Desarrollado por [TheBlackMarc](https://github.com/TheBlackMarc).
