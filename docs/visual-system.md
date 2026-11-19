# Sistema visual de Opalaca

Si algo aquí contradice el código, manda el código: corregí este documento en el mismo cambio.

Guía detallada de **«Ópalo de Erandique»**, vigente desde noviembre de 2026.
Las reglas breves y obligatorias están en [`AGENTS.md`](../AGENTS.md).
El sistema adapta el collage editorial de [El cuaderno](https://github.com/carlosmvks1/carlosmvks1.github.io/blob/625ea2c25f05421892ad332adcf0be57653d7186/docs/visual-system.md)
a una identidad de día. La implementación vive en [`motor/collage.py`](../motor/collage.py)
y las composiciones en [`opalaca.py`](../opalaca.py).

---

## 1. Dirección

Opalaca (@opalacajoyeria) es una joyería por Instagram en Tegucigalpa, Honduras.
Piezas de tendencia y accesibles, normalmente entre L250 y L800, para mujeres
jóvenes y personas que buscan regalos. Hay disponibilidad inmediata y encargos.

La Sierra de Opalaca, en Intibucá y Lempira, da el nombre a la marca. Cerca, en
Erandique (Lempira), se extrae ópalo, incluido el ópalo matrix hondureño. Esa
historia inspira el color y la identidad; no describe el origen de las joyas.

La firma visual es **lugar hondureño en duotono + joya a color + un ópalo de
papel**. El paisaje establece una raíz y la pieza conserva su aspecto real.

## 2. Carácter

Diurno, cálido, cercano y editorial. Papel crema con grano, superposiciones,
cortes contenidos y cambios de escala. Conservar el collage y su riqueza;
el aire y los datos legibles evitan que parezca un catálogo recargado.
La textura es de papel; el ópalo se representa con papeles superpuestos, sin
brillos digitales ni degradados.

---

## 3. Paleta

Valores exactos en `motor.collage.C`, antes del grano:

| Nombre | Hex | Uso |
|---|---|---|
| crema | `#F6F0E8` | Fondo y luces del duotono |
| papel | `#FAF6F0` | Rótulos y etiquetas neutras |
| tinta | `#2B2622` | Texto y sombras del duotono |
| lavanda | `#D6CCEC` | Ópalo; tira de presupuesto |
| menta | `#C4E6DE` | Ópalo; etiqueta secundaria |
| durazno | `#F4CDB6` | Ópalo |
| oro | `#B8913F` | Marca y etiqueta de precio/estado |

### Pino de la sierra

Solo para campaña de diciembre: `--tema navidad` cambia fondo a `#1F3A2E`,
texto sobre el fondo a `#F6F0E8`, oro a `#D4B26A` y acento secundario a
salvia `#5E7D6A`. Las tiras de la guía usan salvia con texto crema. Los papeles
neutros y las etiquetas oro conservan texto tinta para mantener legibilidad. El ópalo
conserva sus tres pasteles y el lugar sigue en duotono tinta → crema.
El flag es explícito, no se activa según el calendario.

## 4. Sistema de collage

### 4.1 Tratamiento fotográfico

| Recurso | Tratamiento | Función |
|---|---|---|
| Lugar hondureño, incluso nocturno | Recorte proporcional y duotono tinta → crema, contraste 1.25 | `fit`, `duotone`, `piece` |
| Joya PNG con transparencia real | Conserva RGB y alfa, orientación EXIF aplicada | `pieza` |
| Joya con fondo liso | Máscara por diferencia con esquinas superiores; RGB intacto | `pieza`, `silhouette` |
| Joya sin foto | Argollas ilustradas, aviso en consola y en imagen | `aretes_marcador` |

La separación automática exige fondo uniforme y suficiente contraste. Revisá
si se pierden detalles o quedan halos; para metal claro sobre blanco prepará
un PNG recortado. No aplicar duotono a la joya. El grano final afecta a toda
la composición, sin convertir la foto de producto a otra paleta.

### 4.2 Reglas de composición

1. Fondo crema, grano 10; al guardar, grano final 6.
2. Un motivo de ópalo por lámina: lavanda de diámetro `d`, menta de `0.62d`
   en `(0.30d, 0.06d)` y durazno de `0.38d` en `(0.12d, 0.52d)`.
   Se construye exclusivamente con `disc()`, borde cortado a mano.
3. Máximo dos **acentos planos** fuera del ópalo. Crema, papel y tinta son
   neutros; la palabra OPALACA es una firma constante. Producto usa oro;
   encargo, oro y menta; guía, lavanda y menta. Historia no añade acentos.
4. Cortes rectos; máximo un borde rasgado por pieza. Las etiquetas tienen
   lados rectos (se corrige el recorte bilateral que tenía el motor del blog).
5. Sombra corta: desplazamiento `(5, 7)`, desenfoque 3 px, opacidad 60 %.
   Rotación absoluta máxima 3°. Las composiciones actuales usan −1°, 1° y 1.5°.
6. Un rótulo en Fraunces cursiva. En producto es la frase en voseo; en guía,
   el título; en historia, la pregunta. Texto narrativo en Fraunces Semi;
   material, precio, estado y presupuesto en Public Sans Semi.
7. OPALACA en mayúsculas, 26 px, oro, arriba a la izquierda `(80, 80)`;
   espaciado adicional 9 px entre letras.
8. Margen de al menos 80 px, incluidas sombras y rectángulos rotados.
   La composición rechaza elementos fuera del área segura.
9. Siempre cuatro datos en producto: tipo/nombre, material exacto, precio
   y estado. `tipo` es opcional; sin él se muestra `nombre` sin guiones.
   El bloque inferior ocupa hasta 1214 px en feed: precio a 60 px (mínimo 46)
   y estado a 46 px en dos líneas sobre un panel oro; material a 40 px
   (mínimo 36). Encargo sube ese bloque 50 px y reserva el anticipo debajo.
10. No recortar textos ni reducirlos bajo los mínimos para hacerlos caber.
    Si no alcanzan, la CLI falla y pide un texto menor. Historia usa 42 px
    para el relato (mínimo 40), con hasta 40 palabras; el título también tiene
    mínimo 40 px. La marca y las notas de muestra conservan su escala propia.
11. En producto y encargo la figura visible de la joya, sin el relleno
    transparente, ocupa al menos 486 px (45 % de 1080) y se centra en x=540.
    Se ajusta proporcionalmente dentro de un área de 720 × 550 px en feed,
    más altura en historia. Una toma demasiado estrecha genera un error:
    hay que aportar una composición más ancha, sin deformar ni cortar la joya.
12. El lugar es un fondo parcial detrás de la joya: 560 × 300 px en A/B,
    300 × 490 px en C, antes de rotación, para feed. El ópalo baja a 270 px.
    En historia aumenta la altura disponible sin estirar los recursos.

### 4.3 Recursos opcionales

La guía admite dos o tres fotos pequeñas de joyas encima del paisaje.
No son obligatorias. El motor conserva `crop_frac`, `circle_window`, `cut_piece`
y `slab` para futuros recortes sin duplicar lógica. Su disponibilidad no
habilita añadir más ópalos, colores o rótulos a las plantillas vigentes.

### 4.4 Formatos y archivos

| Formato | Tamaño | Activación | Destino predeterminado |
|---|---|---|---|
| Feed | 1080 × 1350, 4:5 | Sin flags | `salida/muestras/` |
| Historia | 1080 × 1920, 9:16 | `--historia` | `salida/historias/` |
| Navidad feed | 1080 × 1350 | `--tema navidad` | `salida/navidad/` |
| Navidad historia | 1080 × 1920 | Ambos flags | `salida/historias-navidad/` |

Siempre PNG RGB. Historia recompone alturas y posiciones, sin estirar ni
recortar el feed. `--salida` permite elegir otra carpeta. Cada PNG tiene un
pie `.txt`. Además, cada ejecución escribe `hoja.png`: cuadrícula 3 × N
con todas las láminas generadas en esa ejecución, incluidos los interiores del
carrusel, en orden YAML. Celdas de 360 × 450 px para feed, 360 × 640 para
historia; sin recorte ni rótulos, con celdas finales vacías en crema. No es un
post para publicar. Se arma desde los PNG finales, sin incorporar archivos
antiguos ni una hoja previa. Con `--solo` muestra solo la selección.
Solo `salida/muestras/` se versiona. El grano cambia al regenerar,
aunque los bordes usan semillas fijas. No regenerar muestras sin necesidad.

---

## 5. Plantillas

Los datos viven en [`posts/ejemplos.yaml`](../posts/ejemplos.yaml).
`nombre` es un identificador único: minúsculas, dígitos y guiones.
Todas las entradas incluyen `nombre`, `plantilla` y `lugar`.
Las rutas de imágenes son relativas a la raíz del repo o absolutas.

| Plantilla | Composición | Campos adicionales |
|---|---|---|
| `producto` | Joya centrada y dominante; lugar pequeño detrás, layout A/B/C; ópalo y jerarquía comercial inferior | `pieza` (puede faltar), `frase`, `material`, `precio`, `estado`; opcionales `tipo`, `layout` |
| `encargo` | Producto más etiqueta menta «50 % de anticipo» | Igual a producto; `estado: por encargo · N días`, N entero positivo |
| `guia` | Título grande arriba; ópalo arriba a la derecha; foto al centro; presupuesto en lavanda y etiqueta menta | `titulo`, `rango`; opcional `piezas` (2–3 rutas o null) |
| `historia` | Pregunta, montaña en duotono, ópalo y relato a ≥40 px | `lugar` obligatorio y existente, `titulo`, `texto` de hasta 40 palabras |
| `carrusel` | Portada guía y una lámina producto por pieza | `titulo`, `rango`, `piezas` (lista de mapas de producto) |

Estado admite `disponible` o `por encargo · N días`. Precios como `L350` o
`L350.00`. El precio nunca se inventa si falta. No se comprueba stock real.
En carrusel, cada pieza hereda `lugar` de la portada si no define uno propio;
los archivos se numeran `nombre-01.png` (portada), `nombre-02.png`, etc.
`--solo` selecciona el nombre del post o el carrusel completo.

### 5.1 Variantes A, B y C

| Layout | Foto de fondo | Joya | Ópalo |
|---|---|---|---|
| A | Arriba, desplazada a la izquierda | Centrada, se superpone por debajo de la foto | Abajo a la derecha |
| B | A la derecha, algo más baja; composición en espejo sin reflejar la fotografía | Centrada | Abajo a la izquierda |
| C | Recorte vertical a la izquierda | Centrada sobre el fragmento lateral | Arriba a la derecha |

Los productos y encargos rotan A → B → C según su orden en el YAML, incluyendo
las piezas del carrusel. Guías e historias no consumen un turno de esa rotación.
`layout: A` (o B/C) fuerza una variante. La elección automática evita la
variante anterior y una variante forzada inmediatamente después. Dos productos
consecutivos que fuercen el mismo layout son un error que hay que corregir.
La asignación se hace antes de `--solo`: regenerar una pieza aislada conserva
su layout. No se modifica ni reordena el YAML.

También se revisan los lugares en todas las láminas consecutivas, incluida la
portada del carrusel. Repetir la misma ruta de foto, normalizada, imprime una
**ADVERTENCIA** con ambos nombres y detiene el lote antes de escribir. Cambiá
el lugar en los datos; el motor no elige otra foto por su cuenta. En carruseles
con varias piezas hay que alternar `lugar` explícitamente cuando la herencia
repetiría la foto anterior. La validación incluye el YAML completo con `--solo`.
`hoja` se reserva como nombre de archivo.

## 6. Tono de voz

Voseo hondureño, cálido y breve: «para vos», «eso sos vos», «la que te faltaba»,
«para regalar». Sin lenguaje de lujo inaccesible ni promesas no verificadas.

**Precio siempre visible** en productos; en guías se ve el presupuesto.
La historia de marca no anuncia un producto ni necesita un precio inventado.

Los pies de foto terminan con **«📩 Escribinos al WhatsApp del perfil»**.
La CLI genera estos pies, con datos, nota de marcador cuando aplica y créditos
para las dos fotos de muestra. Agregá los créditos de cualquier otra foto
antes de publicar. Los datos de ejemplos no confirman precio ni disponibilidad.

## 7. Fotografías

Fotos propias primero, con ubicación verificada. Guardar derivados sin GPS
ni otros datos personales; los originales privados no van al repo público.
Para incorporar fotos propias, registrá autor, lugar, permiso y restricciones
en [`fuentes/CREDITOS.md`](../fuentes/CREDITOS.md).

Fotos de proveedor solo con autorización registrada. No publicar personas
reconocibles sin permiso, aunque la foto tenga una licencia libre.

Las muestras usan únicamente las dos fotografías de Wikimedia copiadas del
blog. Se conserva su atribución y licencia. El Picacho está en Tegucigalpa:
la muestra de historia **no documenta la Sierra de Opalaca ni Erandique**.
El TODO en `posts/ejemplos.yaml` pide a Carlos una foto propia del occidente
(Intibucá o Lempira), con ubicación y permiso registrados, para sustituir
El Picacho. Mientras no esté disponible, se conserva como muestra temporal.
Las composiciones con `calle.jpg` son adaptaciones bajo CC BY-SA 4.0;
acompañarlas siempre con sus créditos y declaración de modificaciones.

## 8. Honestidad

No afirmar que las joyas son hechas en Honduras o contienen ópalo salvo que
esté confirmado. La inspiración hondureña está en la estética e historia.
El material siempre es exacto: **oro laminado**, **oro 14K**, **plata 925** o
**acero**, según la pieza real. Nunca convertir «oro laminado» en «oro».

Los marcadores son ilustraciones de posición, no imágenes de la mercancía.
Se identifican en imagen, consola y pie. Antes de publicar, reemplazarlos por
fotos autorizadas y confirmar los datos comerciales.

## 9. Lo que se evita

Banderas, mapas, cinco estrellas, patrones indígenas como decoración genérica,
neón, degradados y lujo exagerado. Imágenes genéricas o generadas por IA
presentadas como lugares hondureños. Fotos de joyas alteradas para cambiar
su material, color o apariencia. Más rótulos, adornos o colores de los que
permite el sistema.
