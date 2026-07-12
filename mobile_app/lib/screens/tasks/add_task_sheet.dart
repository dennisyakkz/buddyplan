import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/network_utils.dart';
import '../../models/repeat_settings.dart';
import '../../models/task_item.dart';
import '../../providers/task_users_provider.dart';
import '../../providers/tasks_provider.dart';
import '../../widgets/repeat_settings_field.dart';

class AddTaskSheet extends ConsumerStatefulWidget {
  final DateTime initialDate;
  final void Function(TaskItem) onSaved;

  const AddTaskSheet(
      {super.key, required this.initialDate, required this.onSaved});

  @override
  ConsumerState<AddTaskSheet> createState() => _AddTaskSheetState();
}

class _AddTaskSheetState extends ConsumerState<AddTaskSheet> {
  final _formKey = GlobalKey<FormState>();
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  late DateTime _date;
  int? _personId;
  RepeatSettings _repeat = const RepeatSettings();
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _date = widget.initialDate;
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  String _fmtDate(DateTime d) =>
      DateFormat('d MMMM yyyy', 'nl_NL').format(d);

  String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    final users = ref
        .watch(taskUsersProvider)
        .users
        .where((u) => u.canManageTasks)
        .toList();
    if (_personId == null && users.isNotEmpty) {
      _personId = users.first.id;
    }

    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
      ),
      child: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Nieuwe taak',
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _titleCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Titel', border: OutlineInputBorder()),
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Verplicht' : null,
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _descCtrl,
                  decoration: const InputDecoration(
                      labelText: 'Omschrijving (optioneel)',
                      border: OutlineInputBorder()),
                  maxLines: 2,
                ),
                const SizedBox(height: 12),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.calendar_today),
                  title: Text(_fmtDate(_date)),
                  onTap: () async {
                    final picked = await showDatePicker(
                      context: context,
                      initialDate: _date,
                      firstDate: DateTime(2020),
                      lastDate: DateTime(2030),
                      locale: const Locale('nl'),
                    );
                    if (picked != null) setState(() => _date = picked);
                  },
                ),
                RepeatSettingsField(
                  anchorDate: _date,
                  value: _repeat,
                  onChanged: (v) => setState(() => _repeat = v),
                ),
                if (users.length > 1) ...[
                  DropdownButtonFormField<int>(
                    decoration: const InputDecoration(
                        labelText: 'Persoon',
                        border: OutlineInputBorder()),
                    value: _personId,
                    items: users
                        .map((u) => DropdownMenuItem(
                              value: u.id,
                              child: Row(children: [
                                CircleAvatar(
                                    backgroundColor: u.color, radius: 6),
                                const SizedBox(width: 8),
                                Text(u.name),
                              ]),
                            ))
                        .toList(),
                    onChanged: (v) => setState(() => _personId = v),
                  ),
                ],
                if (users.isEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Je hebt geen rechten om taken toe te voegen.',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
                if (_error != null) ...[
                  const SizedBox(height: 8),
                  Text(_error!,
                      style: const TextStyle(color: Colors.red)),
                ],
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: (_saving || users.isEmpty) ? null : _save,
                  child: _saving
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(
                              strokeWidth: 2, color: Colors.white))
                      : const Text('Opslaan'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    if (_personId == null) {
      setState(() => _error = 'Kies een persoon');
      return;
    }
    final repeatError = _repeat.validate(_date);
    if (repeatError != null) {
      setState(() => _error = repeatError);
      return;
    }
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      final data = {
        'title': _titleCtrl.text.trim(),
        'description': _descCtrl.text.trim(),
        'anchor_date': _isoDate(_date),
        'icon': 'check',
        ..._repeat.toApiPayload(),
      };
      final localId = 'local-${DateTime.now().millisecondsSinceEpoch}';
      final task = TaskItem(
        id: localId,
        title: _titleCtrl.text.trim(),
        description: _descCtrl.text.trim(),
        icon: 'check',
        personId: _personId,
        date: _date,
        completed: false,
      );
      await ref.read(tasksProvider.notifier).addTaskWithPayload(
            personId: _personId!,
            apiPayload: data,
            optimistic: task,
          );
      widget.onSaved(task);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      setState(() {
        _saving = false;
        _error = isNetworkError(e)
            ? 'Opgeslagen voor later synchroniseren'
            : 'Opslaan mislukt: $e';
      });
      if (isNetworkError(e) && mounted) Navigator.pop(context);
    }
  }
}
