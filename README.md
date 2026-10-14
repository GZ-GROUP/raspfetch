# RASPFETCH

Herramienta de administración para Raspberry Pi. Permite consultar información del sistema,
diagnosticar la conexión a la red local y realizar configuraciones básicas desde la terminal.

**Integrantes:** Ian, Raúl

## Estructura

| Archivo | Contenido |
|---|---|
| `main.py` | Menú interactivo (interfaz de texto con Textual). Ejecuta el script de cada acción y muestra su resultado. |
| `feature1.sh` … `feature10.sh` | Un script Bash por acción. Cada uno define una función y la ejecuta. |
| `requirements.txt` | Dependencias de Python para el menú. |

Los scripts trabajan sobre el **directorio de trabajo**: la carpeta desde donde se ejecuta la
herramienta. Debe estar dentro del directorio personal (`$HOME`) y no se necesita `sudo`.

## Guía de ejecución

### 1. Instalar las dependencias (una sola vez)

En la Raspberry Pi, con Internet:

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

Como el laboratorio no tiene Internet, se pueden descargar los paquetes en otro equipo y
copiarlos a la Raspberry Pi (son paquetes de Python puro, sirven para cualquier arquitectura):

```bash
# En un equipo con Internet
pip download -r requirements.txt -d paquetes
# En la Raspberry Pi, después de copiar la carpeta "paquetes"
python3 -m venv venv
venv/bin/pip install --no-index --find-links paquetes -r requirements.txt
```

### 2. Ejecutar

```bash
cd ~/sistemas-operativos
venv/bin/python main.py
```

| Tecla | Acción |
|---|---|
| `↑` `↓` | Moverse por el menú |
| `Enter` | Ejecutar la acción seleccionada |
| `Tab` | Cambiar de campo dentro de un diálogo |
| `Esc` | Cerrar el panel de resultados o cancelar un diálogo |
| `q` o la opción **0. Salir** | Salir de la herramienta |

Cada script también se puede ejecutar por separado, por ejemplo:

```bash
bash feature5.sh 192.168.1.20          # prueba de conectividad
bash feature8.sh mi_carpeta            # crea ./mi_carpeta
bash feature9.sh archivo_prueba.txt lectura
```

## Acciones y comandos utilizados

| N.º | Acción | Script | Comandos | Función de los comandos |
|---|---|---|---|---|
| 1 | Información del sistema | `feature1.sh` | `hostname`, `uname -r`, `uname -m`, `uptime -p`, `uptime -s` | Nombre del equipo, versión del kernel, arquitectura, tiempo encendido y hora de arranque. |
| 2 | Diagnóstico de memoria | `feature2.sh` | `free -m`, `free -h`, `awk` | RAM total, utilizada y disponible; `awk` extrae los valores para calcular el porcentaje. |
| 3 | Diagnóstico de almacenamiento | `feature3.sh` | `df -hP /`, `df -h -x tmpfs …` | Uso del sistema de archivos raíz y de los demás sistemas de archivos reales. |
| 4 | Configuración de red | `feature4.sh` | `ip -br address`, `ip route` | Interfaces con su estado y direcciones IP, rutas y puerta de enlace. |
| 5 | Prueba de conectividad | `feature5.sh` | `ping -c 4 -W 2 <ip>` | Envía 4 paquetes a otro equipo de la LAN; antes valida que la IP tenga formato IPv4. |
| 6 | Temperatura del procesador | `feature6.sh` | `vcgencmd measure_temp`, `/sys/class/thermal/thermal_zone0/temp` | Temperatura en °C; si no hay sensor lo indica. |
| 7 | Procesos activos | `feature7.sh` | `ps -eo pid,user,%cpu,%mem,comm --sort=-%cpu`, `/proc/loadavg` | Número de procesos, carga promedio y procesos que más CPU y memoria consumen. |
| 8 | Creación de directorios | `feature8.sh` | `mkdir`, `realpath`, `ls -ld` | Crea la carpeta dentro del directorio de trabajo (se elige el destino en un árbol). |
| 9 | Configuración de permisos | `feature9.sh` | `chmod u+r,u-w`, `chmod u+rw`, `ls -l`, `stat -c %a` | Solo lectura o lectura y escritura para el propietario, y comprobación de ambos permisos. |
| 10 | Informe de diagnóstico | `feature10.sh` | `date`, `whoami`, `hostname` y los scripts 1, 2, 3, 4 y 6 | Guarda el resumen en `informe_diagnostico.txt`. |

## Validaciones

- **Prueba de conectividad:** rechaza una IP vacía o con formato incorrecto (por ejemplo `300.1.1.1`).
- **Creación de directorios:** rechaza nombres vacíos, con espacios o caracteres especiales, `.` y `..`,
  carpetas que ya existen y destinos fuera del directorio de trabajo.
- **Configuración de permisos:** rechaza carpetas, archivos fuera del directorio de trabajo,
  archivos de otro propietario y modos que no sean `lectura` o `escritura`.
- Las acciones que crean archivos o carpetas se niegan a ejecutarse fuera de `$HOME`.

## Prueba de permisos

La acción 9 crea `archivo_prueba.txt` en el directorio de trabajo, si todavía no existe, y lo
selecciona por defecto. En el árbol se puede elegir otro archivo.

1. Elegir **Solo lectura**: `ls -l` muestra `-r--…`. Se puede leer el contenido, pero al
   intentar agregar una línea la escritura se reporta como **DENEGADA**.
2. Elegir **Lectura y escritura**: `ls -l` muestra `-rw-…`. La herramienta agrega la línea
   `Modificado el …` y muestra el contenido para comprobarlo.

Para comprobarlo manualmente:

```bash
cat archivo_prueba.txt               # lectura
echo "prueba" >> archivo_prueba.txt  # escritura: "Permiso denegado" si es solo lectura
```

Con otros archivos solo se consulta el permiso (`[ -w archivo ]`) para no modificar su contenido.
