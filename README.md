# Proyecto IHC integrado

Este repositorio reúne copias de los componentes del proyecto. Las carpetas originales permanecen en sus ubicaciones anteriores.

## Componentes

- `Unity/`: proyecto Unity. Ábrelo desde Unity Hub seleccionando esta carpeta.
- `Flutter/`: aplicación Flutter de Android y otras plataformas.
- `backend/`: servidor Python original y lógica del juego.
- `UnityRelay/`: relay WebSocket para comunicar Flutter con Unity.
- `docs/`: guías y especificaciones del proyecto.

Se excluyeron carpetas generadas por Unity, Flutter y Python (como `Library`, `build`, `.dart_tool` y `venv`), la base local `backend/partida.db` y los archivos de entorno o calibración local. Se regeneran al abrir o compilar cada componente.
