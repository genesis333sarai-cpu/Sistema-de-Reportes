# Sistema de Reporte de Incidentes Medio Ambientales — Vinto (MVP)

Taller de Programación · Universidad Adventista de Bolivia
Python + NiceGUI + SQLModel · Arquitectura hexagonal (monolito modular)

## Ejecutar
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate      Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python main.py            # abre http://localhost:8080
pytest -v                 # pruebas de dominio y casos de uso
```

## Usuarios de demostración (se crean en la primera ejecución)
| Rol | CI | Contraseña |
|---|---|---|
| Administrador | 1000001 | admin123 |
| Funcionario municipal | 1000002 | func123 |
| Responsable de atención | 1000003 | resp123 |
| Ciudadano | 1000004 | ciud123 |

Cambie estas contraseñas antes de un uso real, o arranque con `VINTO_SIN_DEMO=1` para no crearlos.
Variables opcionales: `VINTO_DB`, `VINTO_UPLOADS`, `VINTO_SECRET`, `PORT`.

## Estructura
```
main.py                      arranque
app/container.py             raíz de composición (único lugar que elige implementaciones)
app/domain/                  entidades, objetos de valor, reglas, IncidenteFactory
app/application/             puertos (ports.py) y casos de uso
app/infrastructure/          SQLModel, OpenStreetMapAdapter, almacén de archivos, hash
app/ui/                      páginas NiceGUI, tabla con filtros, control de acceso por rol
tests/                       PyTest con repositorios en memoria
```

## Requerimientos funcionales -> dónde viven
| RF | Caso de uso / módulo | Pantalla |
|---|---|---|
| RF-01 Registro | RegistrarIncidenteUseCase | /nuevo |
| RF-02 Categorías | IncidenteFactory, GestionarCategoriasUseCase | /nuevo, /admin |
| RF-03 Ubicación | Coordenada (objeto de valor) | /nuevo (clic en el mapa) |
| RF-04 Fotos | validar_imagen, AlmacenEvidenciaPort | /nuevo |
| RF-05 Filtros | ListarIncidentesUseCase + FiltroIncidentes | /panel, /, /asignaciones |
| RF-06 Estados | CambiarEstadoUseCase, TRANSICIONES | /incidente/{codigo} |
| RF-07 Responsables | AsignarResponsableUseCase | /incidente/{codigo} |
| RF-08 Mapa | MapaPort / OpenStreetMapAdapter | /mapa |
| RF-09 Estadísticas | ObtenerEstadisticasUseCase | /panel, /estadisticas |
| RF-10 Roles | exigir_rol (casos de uso) + exigir (UI) | /login, /admin |
