# Opalaca · reglas obligatorias

Leé [docs/visual-system.md](docs/visual-system.md) antes de cambiar el diseño.
Motor único en `motor/collage.py`, datos en YAML. No dupliqués sus funciones.

1. Lugar hondureño real en duotono tinta → crema, contraste 1.2–1.3; nunca a color.
2. La joya conserva su color original y es la única fotografía a todo color.
3. Un solo motivo de ópalo por post (tres discos superpuestos).
4. Máximo dos acentos planos fuera del ópalo, además de los neutros y la marca.
5. Cortes rectos, como mucho un borde rasgado por pieza.
6. Sombra de 5 × 7 px, desenfoque 3 px, opacidad 60 %; rotaciones ≤ 3°.
7. Un rótulo en Fraunces cursiva; datos en Public Sans. Frases breves en voseo.
8. OPALACA arriba a la izquierda, oro, espaciado de 9 px.
9. Margen mínimo 80 px, incluidas piezas rotadas y sombras.
10. Producto: tipo o nombre, material exacto, precio y estado siempre visibles.
11. Fondo crema con grano 10; grano final 6. Feed 1080 × 1350; historia 1080 × 1920.
12. Navidad es una variante explícita, nunca reemplaza la identidad principal.
13. Producto/encargo: joya visible centrada y ≥45 % del ancho (486 px), sin
    deformar; lugar pequeño como fondo parcial. Layouts A/B/C rotan por YAML;
    `layout` puede forzar uno. Nunca repetir layouts consecutivos de producto.
14. Precio y estado ≥46 px; material ≥36 px. Historia: relato y título ≥40 px,
    `lugar` obligatorio. No reducir estos mínimos para acomodar textos largos.
15. Lugares consecutivos repetidos: avisar con nombres y detener el lote hasta
    corregir el YAML. No sustituir fotos silenciosamente. `--solo` conserva layout.
16. Regenerar `salida/muestras/hoja.png` en 3 columnas desde los PNG finales,
    en orden YAML e incluyendo el carrusel, sin incluir hojas previas.

No afirmar origen hondureño de las piezas ni presencia de ópalo sin evidencia.
No abreviar oro laminado a oro. No publicar personas reconocibles sin permiso.
Fotos propias primero; proveedor solo con autorización. Registrar toda foto en
`fuentes/CREDITOS.md`. No presentar imágenes genéricas o IA como lugares reales.
Sin banderas, mapas, cinco estrellas, patrones indígenas genéricos, neón,
degradados ni lujo exagerado. No incluir originales privados ni metadatos GPS.
Los marcadores no son productos: conservar la advertencia visible y en consola.

Si cambiás el código, actualizá la guía en el mismo cambio. Comprobá con
`python -m unittest discover -s tests -v`, generá las muestras y abrí cada imagen.
No regenerar binarios que no cambiaron: el grano se sortea en cada ejecución.
