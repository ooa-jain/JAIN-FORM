import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_provider.dart';
import 'screens/login_screen.dart';
import 'screens/teacher_home_screen.dart';
import 'screens/student_home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(ChangeNotifierProvider(
    create: (_) => AuthProvider(),
    child: const AttendanceApp(),
  ));
}

class AttendanceApp extends StatelessWidget {
  const AttendanceApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Attendance System',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF1565C0)),
      useMaterial3: true,
    ),
    home: const SplashScreen(),
  );
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashState();
}

class _SplashState extends State<SplashScreen> {
  @override
  void initState() { super.initState(); _init(); }

  Future<void> _init() async {
    final auth = context.read<AuthProvider>();
    await auth.tryRestoreSession();
    if (!mounted) return;
    await Future.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;
    Widget next = auth.isLoggedIn
        ? (auth.user!.isTeacher ? const TeacherHomeScreen() : const StudentHomeScreen())
        : const LoginScreen();
    Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => next));
  }

  @override
  Widget build(BuildContext context) => const Scaffold(
    backgroundColor: Color(0xFF1565C0),
    body: Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
      Icon(Icons.school, color: Colors.white, size: 72),
      SizedBox(height: 20),
      Text('Attendance System', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold)),
      SizedBox(height: 8),
      Text('Secure · BLE · Real-time', style: TextStyle(color: Color(0xFFBBDEFB), fontSize: 14)),
      SizedBox(height: 48),
      CircularProgressIndicator(color: Colors.white54, strokeWidth: 2),
    ])),
  );
}
