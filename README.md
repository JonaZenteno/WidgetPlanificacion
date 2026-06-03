# Widget Dashboard

Aplicacion de escritorio en Python con enfoque minimalista tipo widget para Windows.

## Caracteristicas

- Ventana compacta, sin bordes y personalizable.
- ToDo con agregar, completar, eliminar y scroll.
- Recordatorios con fecha y hora.
- Popup de alerta propio con acciones: `Posponer 5 min` y `Marcar listo`.
- Menu contextual para opacidad, color de fondo, bloqueo de posicion y modo siempre visible.
- Integracion Win32 para comportamiento tipo widget en escritorio.
- Inicio silencioso opcional en Windows.

## Instalacion

```bash
pip install -r requirements.txt
python main.py
```

En Windows tambien puedes ejecutar `main.pyw` para abrir la interfaz sin consola.

## Desarrollo

### Ejecutar tests

```bash
python -m unittest discover -s tests
```

### Estructura base

- `main.py` y `main.pyw`: puntos de entrada
- `widget_dashboard/`: codigo fuente principal
- `tests/`: pruebas basicas de modelos y persistencia

## Datos del usuario

Los datos de ejecucion ya no se guardan dentro del repositorio.

- Windows: `%APPDATA%\WidgetDashboard`
- Otros sistemas: `.widget_dashboard/` dentro del proyecto

Se almacenan ahi:

- `tasks.json`
- `reminders.json`
- `config.json`

Si existe una carpeta `data/` antigua dentro del proyecto, la app migra automaticamente esos archivos la primera vez.

## Autoinicio en Windows

El autoinicio no se habilita por defecto en el codigo publicado.

Si quieres activarlo manualmente:

1. desde la propia app si agregas esa accion al menu, o
2. creando un lanzador silencioso con `pythonw.exe` y `main.pyw`, o
3. empaquetando la app como `.exe` sin consola.

### Instalacion estable recomendada

Para uso diario en Windows, la opcion mas estable es:

1. compilar o usar `WidgetDashboard.exe`
2. copiarlo a una ruta fija, por ejemplo:

```text
C:\Apps\WidgetDashboard\WidgetDashboard.exe
```

3. configurar el autoinicio silencioso apuntando a esa ruta

Ejemplo de `widget_dashboard_start.vbs` en la carpeta `Startup`:

```vbscript
Set shell = CreateObject("WScript.Shell")
shell.Run Chr(34) & "C:\Apps\WidgetDashboard\WidgetDashboard.exe" & Chr(34), 0, False
Set shell = Nothing
```

De esta forma el autoinicio ya no depende del codigo fuente ni de `python.exe`.

### Script Python o `.bat`

Opciones recomendadas:

1. Cambiar el punto de entrada a `main.pyw`.
2. Ejecutar con `pythonw.exe` en lugar de `python.exe`.

Ejemplo:

```bat
start "" "C:\Ruta\Python\pythonw.exe" "C:\Ruta\Proyecto\main.pyw"
```

### Ejecutable con PyInstaller

```bash
pyinstaller --noconsole main.py
```

o:

```bash
pyinstaller -w main.py
```

## Notas de Windows

- El modo de escritorio usa `WorkerW` como mejor esfuerzo.
- Si Windows no lo permite, la app hace fallback al modo estable y la envia al fondo.
- La integracion con el shell de Windows puede variar segun la version del sistema.

## Estructura

```text
main.py
main.pyw
widget_dashboard/
  app.py
  models.py
  persistence/
  services/
  modules/
  ui/
```
