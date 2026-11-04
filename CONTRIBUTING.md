# Cómo trabajamos

## Ramas
- `main` siempre debe funcionar. Nadie sube directo a `main`.
- Una rama por historia de usuario, con el número de la tarjeta: `hu-03-modelo-dw`, `hu-08-etl`, `hu-14-plugin`.

```bash
git checkout main && git pull
git checkout -b hu-08-etl
# ...trabajar...
git add datos/etl/etl.py
git commit -m "HU-08: extraer ventas de la tienda"
git push -u origin hu-08-etl
```

## Pull requests
1. Abrir el pull request en GitHub hacia `main` y llenar la plantilla.
2. Otra persona lo revisa y lo aprueba.
3. Se une (merge) y se borra la rama. Mover la tarjeta de Trello a Done.

Antes de empezar cada día: `git checkout main && git pull`. Evita la mayoría de los conflictos.

## Commits
Pequeños y con un mensaje claro que empiece con la historia: `HU-08: validar que no haya correos repetidos`.

## Seguridad
- Nunca subir contraseñas, claves de API ni cadenas de conexión. Usar `.env` (ya está en `.gitignore`).
- Si se sube una clave por accidente: cambiarla de inmediato en el servicio. Borrar el commit no basta.
- Solo datos ficticios. Ningún dato personal real.
- Usuarios con el mínimo de permisos: solo lectura donde baste.

## Revisión rápida de un pull request
- ¿Corre? ¿Tiene prueba o forma de comprobarlo?
- ¿Hay secretos en el cambio?
- ¿Se entiende sin preguntarle a quien lo escribió?
