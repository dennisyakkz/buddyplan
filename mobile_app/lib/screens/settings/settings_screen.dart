import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../widgets/buddyplan_logo.dart';
import '../../core/preferences.dart';
import '../../providers/auth_provider.dart';
import '../../providers/persons_provider.dart';
import '../../providers/task_users_provider.dart';
import '../../ui/buddyplan_colors.dart';
import '../../widgets/person_settings_row.dart';
import '../../widgets/task_user_settings_row.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late final TextEditingController _urlCtrl;
  late final TextEditingController _userCtrl;
  late final TextEditingController _passCtrl;

  @override
  void initState() {
    super.initState();
    _urlCtrl = TextEditingController(text: AppPreferences.serverUrl);
    _userCtrl = TextEditingController();
    _passCtrl = TextEditingController();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (AppPreferences.authToken?.isNotEmpty == true) {
        ref.read(taskUsersProvider.notifier).load();
        ref.read(personsProvider.notifier).load();
      }
    });
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    _userCtrl.dispose();
    _passCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    final taskUsersState = ref.watch(taskUsersProvider);
    final personsState = ref.watch(personsProvider);
    final isLoginOnly = !auth.isLoggedIn;

    return Scaffold(
      appBar: isLoginOnly
          ? null
          : AppBar(title: const Text('Instellingen')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          if (isLoginOnly) ...[
            const SizedBox(height: 24),
            Center(
              child: const BuddyplanLogo(
                size: 120,
                variant: BuddyplanLogoVariant.color,
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Inloggen',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 32),
          ],
          Text('Server',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          TextField(
            controller: _urlCtrl,
            decoration: const InputDecoration(
              labelText: 'Server URL',
              hintText: 'https://mijnapp.nl',
            ),
            keyboardType: TextInputType.url,
            autocorrect: false,
          ),
          const SizedBox(height: 24),
          if (!isLoginOnly) ...[
            Text('Account',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Icon(Icons.account_circle,
                  color: BuddyplanColors.teal),
              title: Text('Ingelogd als: ${auth.name ?? ''}'),
              trailing: TextButton(
                onPressed: () => ref.read(authProvider.notifier).logout(),
                child: const Text('Uitloggen'),
              ),
            ),
            const SizedBox(height: 24),
          ],
          if (!auth.isLoggedIn) ...[
            TextField(
              controller: _userCtrl,
              decoration: const InputDecoration(
                labelText: 'Gebruikersnaam',
              ),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _passCtrl,
              decoration: const InputDecoration(
                labelText: 'Wachtwoord',
              ),
              obscureText: true,
            ),
            const SizedBox(height: 12),
            if (auth.error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Text(auth.error!,
                    style: const TextStyle(color: Colors.red)),
              ),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: auth.isLoading ? null : _login,
                child: auth.isLoading
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(
                            strokeWidth: 2, color: Colors.white))
                    : const Text('Inloggen'),
              ),
            ),
          ],
          if (auth.isLoggedIn) ...[
            Text('Agenda',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(
              'Kies welke kalenders zichtbaar zijn.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            if (personsState.isLoading)
              const Center(child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ))
            else if (personsState.error != null)
              Text(personsState.error!,
                  style: const TextStyle(color: Colors.red))
            else if (personsState.persons.isEmpty)
              const Text('Geen kalenders gevonden.')
            else
              ...personsState.persons.map(
                (person) => Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: PersonSettingsRow(
                    person: person,
                    showDivider: false,
                  ),
                ),
              ),
            const SizedBox(height: 24),
            Text('Taken',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            Text(
              'Kies welke gebruikers zichtbaar zijn.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            if (taskUsersState.isLoading)
              const Center(child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ))
            else if (taskUsersState.error != null)
              Text(taskUsersState.error!,
                  style: const TextStyle(color: Colors.red))
            else if (taskUsersState.users.isEmpty)
              const Text('Geen gebruikers met taken gevonden.')
            else
              ...taskUsersState.users.map(
                (user) => Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: TaskUserSettingsRow(
                    user: user,
                    showDivider: false,
                  ),
                ),
              ),
          ],
        ],
      ),
    );
  }

  Future<void> _login() async {
    final url = _urlCtrl.text.trim();
    final user = _userCtrl.text.trim();
    final pass = _passCtrl.text;
    if (url.isEmpty || user.isEmpty || pass.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Vul alle velden in')));
      return;
    }
    final ok = await ref.read(authProvider.notifier).login(url, user, pass);
    if (ok && mounted) {
      await ref.read(taskUsersProvider.notifier).load();
      await ref.read(personsProvider.notifier).load();
      Navigator.of(context).pop();
    }
  }
}
