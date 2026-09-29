# Proyecto IHC - Five Nights of Terror

Este es un proyecto/juego que lleva como fuente de origen Five nights at freddys y las mecanicas de las tareas de among us 

## Requisitos 

- Windows 10/11 para ejecutar el relay(servidor)y Unity en la computadora.
- **Unity Hub** y **Unity Editor 2022.3.30f1**. La versión requerida está en `Unity/ProjectSettings/ProjectVersion.txt`.
- **Python 3.10 o superior** y `pip`, para ejecutar `UnityRelay/relay.py`.
- **Flutter SDK** con Dart **3.12.2 o superior**; `Flutter/pubspec.yaml` declara `sdk: ^3.12.2`.
- **Android Studio**, Android SDK y Platform Tools. En el teléfono, activa las opciones de modo desarrollador y la depuración USB, tambien se puede usar de forma inalambrica; también puedes usar un emulador Android.
- Computadora y teléfono conectados a la misma red local. Unity necesita acceso a la cámara de la computadora para el seguimiento facial.
- Internet durante la primera resolución de paquetes de Unity y Flutter.
### Paquetes y dependencias

- Unity carga sus paquetes desde `Unity/Packages/manifest.json` y `Unity/Packages/packages-lock.json`. Incluye MediaPipe Unity, NativeWebSocket, AI Navigation y Unity UI, entre otros. Abre el proyecto y espera a que Unity termine de importar los paquetes.
- Flutter descarga las dependencias de `Flutter/pubspec.yaml` mediante `flutter pub get`. Sus dependencias directas son `cupertino_icons`, `web_socket_channel`, `provider`, `flutter_local_notifications`, `vibration`, `flutter_svg`, `lottie`, `logger`, `shared_preferences` y `audioplayers`; las versiones exactas están en ese archivo y las versiones resueltas, en `Flutter/pubspec.lock`. Para desarrollo también usa `flutter_test` y `flutter_lints`.
- El relay solo necesita el paquete Python `websockets`, declarado en `UnityRelay/requirements.txt`.


### 1. Abrir el proyecto Unity

En Unity Hub, elige **Add/Open project from disk** y selecciona la carpeta `Unity/`, no la carpeta contenedora del repositorio. Abre la escena:

`Assets/MediaPipeUnity/Samples/Scenes/Face Landmark Detection/Face Landmark Detection.unity`

Al abrir por primera vez, espera a que Unity resuelva los paquetes y termine la importación. Si la escena no aparece automáticamente, ábrela desde la ventana **Project**.

### 2. Instalar las dependencias Flutter

En una terminal, desde `Flutter/`, ejecuta:

```powershell
flutter doctor
flutter pub get
flutter devices
```

Si es la primera configuración de Android, completa lo que indique `flutter doctor` y acepta las licencias del SDK con `flutter doctor --android-licenses`.

## Cómo iniciar una partida conectada

Mantén abiertas tres ventanas: relay, Unity y Flutter.

### Terminal 1: iniciar el relay

Desde la carpeta raíz del repositorio:

```powershell
cd UnityRelay
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe relay.py
```

La consola debe mostrar `Relay Unity activo en ws://0.0.0.0:8000`. Déjala abierta mientras juegas. La primera vez, Windows Firewall puede pedir permiso para Python; permite el acceso en tu red privada.

### Unity: ejecutar la escena

En Unity, abre la escena indicada arriba y pulsa **Play**. Unity se conecta al relay mediante `ws://127.0.0.1:8000` porque corre en la misma computadora.

### Terminal 2: ejecutar Flutter

Conecta el teléfono por USB con depuración habilitada y, desde `Flutter/`, ejecuta la app en ese dispositivo Android. Usa el identificador Android que aparece en `flutter devices`:

```powershell
flutter run -d <id-del-telefono>
```

Sustituye `<id-del-telefono>` por el identificador mostrado en tu equipo. Así evitas iniciar por error el target Windows de escritorio.

En la app, abre **Opciones**:

1. Desactiva **Modo simulado**.
2. En **IP/servidor**, escribe la IPv4 local de la computadora (puedes verla con `ipconfig`; usa la dirección de la conexión Wi-Fi activa).
3. Deja el puerto en `8000` y guarda.
4. Inicia o continúa la partida desde el menú.

No uses `localhost` ni `127.0.0.1` como IP en el teléfono: allí apuntarían al propio teléfono. Si no conecta, verifica que ambos dispositivos estén en la misma Wi-Fi y que Windows Firewall permita conexiones entrantes al puerto TCP `8000` en una red privada.


## Qué ocurre durante el juego

Flutter inicia la conexión al relay; Unity recibe el mensaje `connect`, ejecuta la noche y envía las tareas y los estados a Flutter. Las tareas se resuelven en el teléfono. Un ataque detiene la partida y muestra el jumpscare con su sonido en Flutter y en la ventana **Game** de Unity. La lógica de rutas, probabilidades y progreso está descrita en `Unity/Assets/scripts/INTEGRACION_UNITY.md`.

