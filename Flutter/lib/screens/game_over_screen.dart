import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/game_provider.dart';
import '../providers/connection_provider.dart';
<<<<<<< HEAD
import 'menu_principal_screen.dart';
=======
import 'splash_screen.dart';
>>>>>>> origin/main

class GameOverScreen extends StatelessWidget {
  const GameOverScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final GameProvider game = context.watch<GameProvider>();
    final session = game.session;
    final int? noche = game.ultimaNocheDeGameOver;

    return Scaffold(
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('JUEGO TERMINADO',
                style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            if (noche != null) Text('Fallaste en la Noche $noche'),
            const SizedBox(height: 16),
            Text('Tareas completadas: ${session.tasksCompleted}'),
            Text('Tareas fallidas: ${session.tasksFailed}'),
            Text('Puntuación: ${session.score}'),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () {
                context.read<GameProvider>().reset();
                context.read<ConnectionProvider>().disconnect();
                Navigator.of(context).pushAndRemoveUntil(
                  MaterialPageRoute<void>(
<<<<<<< HEAD
                    builder: (_) => const MenuPrincipalScreen(),
=======
                    builder: (_) => const SplashScreen(modo: 'continuar'),
>>>>>>> origin/main
                  ),
                  (route) => false,
                );
              },
<<<<<<< HEAD
              child: const Text('Continuar'),
=======
              child: const Text('Reintentar'),
>>>>>>> origin/main
            ),
          ],
        ),
      ),
    );
  }
}
