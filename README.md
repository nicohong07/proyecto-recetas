# Minecraft Crafting Guide API

API REST de recetas de fabricación (*crafting*) inspirada en Minecraft. Cualquier persona puede consultar y buscar recetas. Los usuarios registrados pueden crear sus propias recetas, y editar o eliminar solo las que crearon ellos.

## Tecnologías

- **Python 3.14** + **FastAPI**
- **PostgreSQL 17**
- **SQLAlchemy** (Core, con consultas SQL escritas a mano)
- **PyJWT** para los tokens de autenticación
- **pwdlib** con **Argon2** para el hash de contraseñas
- **Docker** y **Docker Compose**

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (incluye Docker Compose)
- Git

No hace falta instalar Python ni PostgreSQL: todo corre dentro de contenedores.

## Configuración

1. Clonar el repositorio:

```bash
   git clone <url-del-repositorio>
   cd proyecto-recetas
```

2. Crear el archivo `.env` a partir del ejemplo:

```bash
   cp .env.example .env
```

   En Windows (PowerShell): `copy .env.example .env`

3. Completar los valores del `.env`. Para generar una `SECRET_KEY` segura:

```bash
   python -c "import secrets; print(secrets.token_hex(32))"
```

   Si no tenés Python instalado, cualquier texto largo y aleatorio sirve.

## Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `POSTGRES_USER` | Usuario de PostgreSQL | `recipes_user` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `una_contraseña_segura` |
| `POSTGRES_DB` | Nombre de la base de datos | `recipes_DB` |
| `DATABASE_URL` | URL de conexión. Se usa al correr la API fuera de Docker. Dentro de Docker, `docker-compose.yml` la reemplaza para apuntar al servicio `db`. | `postgresql+psycopg://user:pass@localhost:5432/recipes_DB` |
| `SECRET_KEY` | Clave para firmar los tokens JWT. **Nunca debe subirse al repositorio.** | *(texto aleatorio de 64 caracteres)* |
| `ALGORITHM` | Algoritmo de firma de los JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutos de validez de cada token | `30` |

## Iniciar la aplicación

```bash
docker compose up -d --build
```

Esto levanta dos servicios:

| Servicio | Descripción | Puerto |
|---|---|---|
| `db` | PostgreSQL. Los datos se guardan en un volumen, así que persisten aunque se reinicien los contenedores. | `5432` |
| `api` | La API de FastAPI. Espera a que la base esté lista antes de arrancar. | `8000` |

Las tablas se crean automáticamente al iniciar la API.

Comandos útiles:

```bash
docker compose ps          # ver el estado de los servicios
docker compose logs api    # ver los logs de la API
docker compose stop        # detener los servicios (sin borrar nada)
docker compose down        # detener y borrar los contenedores (los datos se mantienen)
docker compose down -v     # detener y borrar todo, incluidos los datos
```

## Documentación interactiva (Swagger)

Con la aplicación corriendo, abrir:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Los endpoints que requieren autenticación aparecen con un candado 🔒.

## Cómo probar la API

### 1. Registrar un usuario

`POST /auth/register`

```json
{
  "username": "steve",
  "password": "diamond123"
}
```

- `username`: entre 5 y 16 caracteres.
- `password`: entre 8 y 64 caracteres.

### 2. Iniciar sesión desde Swagger

1. Tocar el botón **Authorize** (arriba a la derecha).
2. Completar `username` y `password`. Los demás campos (`client_id`, `client_secret`) se pueden dejar vacíos.
3. Tocar **Authorize**.

Swagger obtiene el token y lo envía automáticamente en cada request a un endpoint protegido.

Desde otro cliente (Postman, curl, etc.), el login es un formulario en `POST /auth/login`, y el token devuelto se envía en el header:

```
Authorization: Bearer <access_token>
```

### 3. Crear una receta

`POST /recipes` (requiere autenticación)

```json
{
  "name": "Iron Pickaxe",
  "result_item": "iron_pickaxe",
  "result_quantity": 1,
  "crafting_station": "crafting_table",
  "ingredients": [
    { "item": "iron_ingot", "quantity": 3 },
    { "item": "stick", "quantity": 2 }
  ]
}
```

Las estaciones disponibles se pueden consultar en `GET /stations`.

### 4. Probar los permisos

Para comprobar que un usuario no puede modificar recetas ajenas: registrar un segundo usuario, cerrar sesión en **Authorize → Logout**, iniciar sesión con el segundo usuario e intentar editar o borrar una receta del primero. La respuesta debe ser `403 Forbidden`.

## Endpoints

| Método | Ruta | Autenticación | Descripción |
|---|---|---|---|
| `POST` | `/auth/register` | No | Registrar un usuario |
| `POST` | `/auth/login` | No | Iniciar sesión y obtener un token JWT |
| `GET` | `/recipes` | No | Listar recetas, con filtros y paginación |
| `GET` | `/recipes/{recipe_id}` | No | Obtener una receta |
| `POST` | `/recipes` | Sí | Crear una receta |
| `PUT` | `/recipes/{recipe_id}` | Sí (solo el autor) | Editar una receta |
| `DELETE` | `/recipes/{recipe_id}` | Sí (solo el autor) | Eliminar una receta |
| `GET` | `/users/me/recipes` | Sí | Listar las recetas del usuario autenticado |
| `GET` | `/stations` | No | Listar las estaciones de fabricación |

### Filtros y paginación

`GET /recipes` acepta estos parámetros de consulta, combinables entre sí:

| Parámetro | Descripción | Por defecto |
|---|---|---|
| `page` | Número de página (desde 1) | `1` |
| `page_size` | Recetas por página (entre 1 y 100) | `10` |
| `name` | Filtra por nombre (contiene, sin distinguir mayúsculas) | — |
| `item` | Filtra recetas que tengan algún ingrediente que coincida | — |

Ejemplo: `GET /recipes?name=pick&item=iron&page=1&page_size=5`

La respuesta incluye la información necesaria para navegar las páginas:

```json
{
  "items": [ ... ],
  "total": 12,
  "page": 1,
  "page_size": 5,
  "total_pages": 3
}
```

### Códigos de respuesta

| Código | Cuándo |
|---|---|
| `200` | Operación exitosa |
| `201` | Recurso creado (usuario o receta) |
| `401` | Falta el token, es inválido o venció; o el usuario o la contraseña son incorrectos |
| `403` | El usuario está autenticado, pero intenta modificar una receta de otro |
| `404` | La receta no existe |
| `409` | El nombre de usuario ya está registrado |
| `422` | Los datos enviados no son válidos (por ejemplo, cantidad 0 o una receta sin ingredientes) |

## Estructura del proyecto

```
proyecto-recetas/
├── app/
│   ├── main.py            # Endpoints (capa HTTP)
│   ├── models.py          # Definición de las tablas (SQLAlchemy)
│   ├── schemas.py         # Modelos de entrada y salida (Pydantic)
│   ├── core/
│   │   ├── config.py      # Lectura de variables de entorno
│   │   └── security.py    # Hash de contraseñas y tokens JWT
│   └── database/
│       ├── database.py    # Conexión a la base de datos
│       └── crud.py        # Consultas SQL
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Decisiones técnicas

**Separación en capas.** Cada parte tiene una sola responsabilidad:

- `main.py` maneja HTTP: recibe los requests, decide los códigos de estado y lanza los errores.
- `crud.py` solo habla con la base de datos. No conoce HTTP: si algo no existe, devuelve `None`, y el endpoint lo traduce a un `404`.
- `security.py` sabe cómo hashear contraseñas y crear o verificar tokens, pero no accede a la base.

**SQL escrito a mano.** Las consultas se escriben con `text()` de SQLAlchemy en lugar de usar el ORM. La decisión fue intencional, para aprender SQL y tener control total sobre las consultas. Todos los valores se pasan como parámetros (`:nombre`), nunca concatenando texto, para evitar inyección SQL. SQLAlchemy se usa para definir las tablas (`models.py`) y para manejar las conexiones y transacciones.

**Transacciones.** Las operaciones de escritura usan `engine.begin()`. Al crear o editar una receta, la receta y sus ingredientes se guardan en la misma transacción: si falla algún ingrediente, no queda una receta a medias.

**Contraseñas.** Se guardan hasheadas con Argon2 (a través de `pwdlib`), que incluye un salt aleatorio en cada hash y es lento a propósito para dificultar ataques de fuerza bruta. La contraseña nunca se devuelve ni se guarda en texto plano. Hay schemas separados para la entrada (`UserCreate`), la salida (`User`) y el uso interno (`UserInDB`), de modo que el hash nunca puede salir en una respuesta.

**Autenticación con JWT.** El login devuelve un token firmado con HS256 que contiene el id del usuario (`sub`) y una fecha de vencimiento (`exp`). El servidor no guarda los tokens: los verifica con la firma. Por eso tienen un vencimiento corto. El login usa un formulario con los campos estándar de OAuth2 (`username` y `password`), lo que permite usar el botón **Authorize** de Swagger.

**Mismo mensaje de error en el login.** Si el usuario no existe o la contraseña es incorrecta, la respuesta es la misma, para no revelar qué nombres de usuario están registrados.

**Permisos.** El autor de una receta se toma del token, nunca del body, así que nadie puede crear recetas a nombre de otro. Al editar o borrar, se verifica primero que la receta exista (`404`) y después que pertenezca al usuario (`403`).

**Usuario único.** La columna `username` es `UNIQUE`. Si se intenta registrar un nombre repetido, PostgreSQL rechaza el `INSERT` y la API responde `409`. Se usa la restricción de la base en lugar de consultar antes, para evitar que dos registros simultáneos con el mismo nombre pasen el chequeo.

**Filtros.** La búsqueda por nombre usa `ILIKE` (sin distinguir mayúsculas). La búsqueda por ingrediente usa una subconsulta `EXISTS`, para devolver las recetas que tengan al menos un ingrediente que coincida, con todos sus ingredientes completos.

**Edición de ingredientes.** Al editar una receta, se borran sus ingredientes y se insertan los nuevos, en lugar de comparar uno por uno cuáles cambiaron.

**Validaciones.** Pydantic valida los datos antes de que lleguen al código: cantidades mayores a 0, al menos un ingrediente y largos máximos acordes a las columnas de la base.

## Posibles mejoras

- **Migraciones con Alembic.** Hoy las tablas se crean con `create_all`, que no modifica tablas existentes. Para cambiar la estructura hay que recrear la base.
- **Tests automatizados** con `pytest`, sobre una base de datos separada.
- Paginación en `GET /users/me/recipes`.
- Datos iniciales de ejemplo (*seed*).

## Recursos utilizados

- [Documentación de FastAPI](https://fastapi.tiangolo.com/), en especial la sección de seguridad con OAuth2 y JWT
- [Documentación de SQLAlchemy](https://docs.sqlalchemy.org/)
- [Documentación de PostgreSQL](https://www.postgresql.org/docs/)
- [Documentación de PyJWT](https://pyjwt.readthedocs.io/)
- [Documentación de pwdlib](https://frankie567.github.io/pwdlib/)
- [Documentación de Docker](https://docs.docker.com/)

## Uso de Inteligencia Artificial

Durante el desarrollo usé **Claude** (Anthropic) como apoyo para:

- Aprender conceptos nuevos: SQL desde Python, transacciones, hash de contraseñas, JWT, OAuth2, `Depends` de FastAPI y Docker.
- Revisar el código que fui escribiendo y encontrar errores.
- Entender mensajes de error durante la depuración.
- Organizar la estructura del proyecto y redactar este README.

El código fue escrito y revisado por mí, con la IA como guía.