import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import 'teacher_home_screen.dart';
import 'student_home_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl  = TextEditingController();
  final _formKey   = GlobalKey<FormState>();
  String _role  = 'student';
  bool _obscure = true;

  @override
  void dispose() { _emailCtrl.dispose(); _passCtrl.dispose(); super.dispose(); }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;
    final auth = context.read<AuthProvider>();
    final ok = await auth.login(_emailCtrl.text.trim(), _passCtrl.text, _role);
    if (ok && mounted) {
      Navigator.pushReplacement(context, MaterialPageRoute(
        builder: (_) => auth.user!.isTeacher ? const TeacherHomeScreen() : const StudentHomeScreen(),
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      backgroundColor: const Color(0xFFF8F9FA),
      body: SafeArea(child: Center(child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 28),
        child: Form(key: _formKey, child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80, height: 80,
              decoration: BoxDecoration(color: const Color(0xFF1565C0), borderRadius: BorderRadius.circular(20)),
              child: const Icon(Icons.school, color: Colors.white, size: 40),
            ),
            const SizedBox(height: 20),
            const Text('Attendance System', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            const Text('BLE-secured attendance', style: TextStyle(color: Color(0xFF888888))),
            const SizedBox(height: 36),

            // Role selector
            Container(
              decoration: BoxDecoration(
                color: Colors.white, borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE0E0E0)),
              ),
              child: Row(children: ['student','teacher'].map((r) {
                final active = _role == r;
                return Expanded(child: GestureDetector(
                  onTap: () => setState(() => _role = r),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 180),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    decoration: BoxDecoration(
                      color: active ? const Color(0xFF1565C0) : Colors.transparent,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(r[0].toUpperCase() + r.substring(1),
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: active ? Colors.white : const Color(0xFF666666),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ));
              }).toList()),
            ),
            const SizedBox(height: 20),

            TextFormField(
              controller: _emailCtrl,
              keyboardType: TextInputType.emailAddress,
              decoration: _decor('Email', Icons.email_outlined),
              validator: (v) => v!.contains('@') ? null : 'Enter valid email',
            ),
            const SizedBox(height: 14),

            TextFormField(
              controller: _passCtrl,
              obscureText: _obscure,
              decoration: _decor('Password', Icons.lock_outline).copyWith(
                suffixIcon: IconButton(
                  icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility, color: Colors.grey),
                  onPressed: () => setState(() => _obscure = !_obscure),
                ),
              ),
              validator: (v) => v!.length >= 6 ? null : 'Min 6 characters',
            ),
            const SizedBox(height: 10),

            if (auth.error != null) Container(
              padding: const EdgeInsets.all(12),
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(color: const Color(0xFFFFEBEE), borderRadius: BorderRadius.circular(8)),
              child: Row(children: [
                const Icon(Icons.error_outline, color: Color(0xFFC62828), size: 18),
                const SizedBox(width: 8),
                Expanded(child: Text(auth.error!, style: const TextStyle(color: Color(0xFFC62828), fontSize: 13))),
              ]),
            ),

            const SizedBox(height: 8),
            SizedBox(width: double.infinity, height: 50,
              child: ElevatedButton(
                onPressed: auth.loading ? null : _login,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1565C0), foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: auth.loading
                    ? const SizedBox(width: 22, height: 22,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('Sign In', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
              ),
            ),

            const SizedBox(height: 24),
            const Text('Test Accounts:', style: TextStyle(color: Color(0xFF888888), fontSize: 12)),
            const Text('Teacher: rajan@college.edu / teacher123', style: TextStyle(fontSize: 12, color: Color(0xFF555555))),
            const Text('Student: arjun@college.edu / student123', style: TextStyle(fontSize: 12, color: Color(0xFF555555))),
          ],
        )),
      ))),
    );
  }

  InputDecoration _decor(String label, IconData icon) => InputDecoration(
    labelText: label,
    prefixIcon: Icon(icon, color: const Color(0xFF1565C0)),
    filled: true, fillColor: Colors.white,
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE0E0E0))),
    enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFFE0E0E0))),
    focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Color(0xFF1565C0), width: 1.5)),
  );
}
