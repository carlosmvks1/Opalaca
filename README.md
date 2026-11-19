# Opalaca · Ópalo de Erandique

Generador local de posts para **@opalacajoyeria**, Tegucigalpa, Honduras.
Un lugar real en duotono, una joya a color y un ópalo de papel. El sistema
adapta el collage de [El cuaderno](https://github.com/carlosmvks1/carlosmvks1.github.io)
a fondo crema y paleta de ópalo. No publica en Instagram.

## Instalar

Python 3.10 o posterior. Desde la carpeta del repo:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

Las tres tipografías OFL y las fotos de muestra vienen incluidas; no hay
servicios externos ni descargas al generar.

## Generar un post

```bash
python opalaca.py posts/ejemplos.yaml
python opalaca.py posts/ejemplos.yaml --solo argollas-oro
python opalaca.py posts/ejemplos.yaml --solo guia-500 --historia
python opalaca.py posts/ejemplos.yaml --tema navidad
python opalaca.py posts/ejemplos.yaml --historia --tema navidad
python opalaca.py posts/ejemplos.yaml --salida salida/mi-campana
```

El primer comando escribe **7 PNG de 1080 × 1350** y sus pies `.txt` en
`salida/muestras/`, más **hoja.png** con todas las láminas en una cuadrícula
3 × N de celdas 360 × 450, en orden YAML. La hoja se rehace con la selección
de cada ejecución (con `--solo`, solo esa selección), sin imágenes antiguas.
`--historia` recompone a 1080 × 1920, en
`salida/historias/`; navidad usa carpetas separadas. `--salida` cambia el destino.
Los PNG del mismo nombre se reemplazan al regenerar. El grano es aleatorio.

El argumento YAML es relativo a tu terminal; las rutas de imágenes son
relativas al repo (también se admiten absolutas). Desde otra carpeta:
`python /ruta/opalaca/opalaca.py /ruta/opalaca/posts/ejemplos.yaml`.

## Crear tus datos

```yaml
- nombre: argollas-oro
  plantilla: producto
  # layout: B  # opcional; por defecto rota A → B → C
  lugar: fuentes/lugares/picacho.jpg
  pieza: fuentes/piezas/argollas.png
  tipo: Argollas
  frase: para vos
  material: oro laminado
  precio: L350
  estado: disponible
```

`nombre` identifica el archivo y `tipo` es el nombre visible; si no hay `tipo`,
se muestra `nombre` sin guiones. Las cinco plantillas están documentadas en
[la guía visual](docs/visual-system.md#5-plantillas) y tienen ejemplos en
[posts/ejemplos.yaml](posts/ejemplos.yaml).

`encargo` exige `por encargo · N días` y añade «50 % de anticipo».
`guia` admite 2 o 3 rutas de piezas opcionales. `historia` limita el relato a
40 palabras. `carrusel` usa una lista de mapas de producto, hereda el lugar
y numera desde `-01` (portada). `--solo favoritos` genera el carrusel entero.
`--historia` es un formato disponible para todas las plantillas, distinto de
la plantilla narrativa `historia`.

Producto y encargo rotan entre tres composiciones: A (foto arriba), B (en
espejo) y C (foto lateral). `layout: A`, B o C fuerza una. La rotación cuenta
los productos del YAML y del carrusel, se calcula antes de `--solo` y evita
repeticiones. Dos layouts forzados iguales consecutivos son un error.

Dos láminas consecutivas tampoco pueden repetir la misma foto de lugar:
la CLI avisa y detiene el lote antes de guardar. Alterná `lugar`, también en
los interiores del carrusel. Se comprueba el YAML completo con `--solo`.

La joya visible ocupa ≥45 % del ancho y está centrada. Si una toma muy estrecha
no cabe a esa escala, la CLI pide una composición más ancha, sin deformarla.
Precio/estado nunca bajan de 46 px, material de 36 px y relato de historia de
40 px. Un texto demasiado largo se rechaza. `lugar` sigue siendo obligatorio;
el TODO de la historia pide una foto propia de Intibucá o Lempira.

La CLI valida campos, nombres duplicados, precios y estados antes de guardar.
Un lugar inexistente es un error. Si falta la foto de una joya, dibuja unas
argollas y avisa en consola, imagen y pie. PNG transparente conserva su alfa;
otras fotos usan separación del fondo liso. Revisá el recorte de metal claro:
si hace falta, usá un PNG recortado. Nunca se pasa la joya por duotono.

**Las muestras no son anuncios listos para publicar:** no hay fotos reales de
joyas ni inventario confirmado. Reemplazá marcadores y datos de demostración.
El Picacho ilustra la composición de la historia; no es una foto de Opalaca.

## Revisar y mantener

```bash
python -m unittest discover -s tests -v
python opalaca.py posts/ejemplos.yaml
```

Abrí cada PNG: tamaño correcto, margen mínimo 80 px, un motivo de ópalo,
máximo dos acentos planos, paisaje en duotono y producto a color. Los textos
largos generan un error en vez de salir del margen. No regenerés muestras
sin cambiar su diseño: el grano nuevo produce cambios binarios.

- [Reglas para agentes](AGENTS.md)
- [Sistema visual completo](docs/visual-system.md)
- [Créditos y permisos](fuentes/CREDITOS.md)
- [Procedencia del motor y licencias de fuentes](motor/ORIGEN.md)
- [Muestras y revisión](salida/muestras/README.md)

La raíz hondureña corresponde a la identidad, no al origen del producto.
Escribí el material exacto y registrá cada foto. Fotos de proveedor y personas
reconocibles requieren permiso. Los pies generados terminan con
«📩 Escribinos al WhatsApp del perfil» e incluyen los créditos de las fotos
Wikimedia de muestra. Para otras fotos, completá la atribución del pie.
