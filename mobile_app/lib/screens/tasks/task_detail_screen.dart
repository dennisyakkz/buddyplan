import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/api_client.dart';
import '../../core/network_utils.dart';
import '../../models/repeat_settings.dart';
import '../../models/task_item.dart';
import '../../models/person.dart';
import '../../providers/tasks_provider.dart';
import '../../widgets/repeat_settings_field.dart';

class TaskDetailScreen extends ConsumerStatefulWidget {
  final TaskItem task;
  final List<Person> persons;
  final bool canEdit;

  const TaskDetailScreen({
    super.key,
    required this.task,
    required this.persons,
    required this.canEdit,
  });

  @override
  ConsumerState<TaskDetailScreen> createState() => _TaskDetailScreenState();
}

class _TaskDetailScreenState extends ConsumerState<TaskDetailScreen> {
  final _titleCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  DateTime? _anchorDate;
  RepeatSettings _repeat = const RepeatSettings();
  bool _loading = true;
  bool _saving = false;
  String? _error;
  int? _apiTaskId;

  bool get _readOnly => !widget.canEdit || _apiTaskId == null;

  @override
  void initState() {
    super.initState();
    _titleCtrl.text = widget.task.title;
    _descCtrl.text = widget.task.description;
    _anchorDate = widget.task.date;
    _apiTaskId = int.tryParse(widget.task.id);
    _loadDetail();
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadDetail() async {
    final id = _apiTaskId;
    if (id == null) {
      setState(() => _loading = false);
      return;
    }
    try {
      final raw = await ApiClient.instance.fetchTaskDetail(id);
      setState(() {
        _titleCtrl.text = raw['title'] as String? ?? widget.task.title;
        _descCtrl.text = raw['description'] as String? ?? '';
        final anchorRaw = raw['anchor_date'] as String?;
        if (anchorRaw != null) {
          _anchorDate = DateTime.parse(anchorRaw);
        }
        _repeat = RepeatSettings.fromApi(raw);
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _error = isNetworkError(e) ? 'Kon taak niet laden' : '$e';
      });
    }
  }

  String _fmtDate(DateTime d) =>
      DateFormat('d MMMM yyyy', 'nl_NL').format(d);

  String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  Person? get _person {
    final id = widget.task.personId;
    if (id == null) return null;
    for (final p in widget.persons) {
      if (p.id == id) return p;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_readOnly ? 'Taak' : 'Taak bewerken'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(24),
              children: [
                if (_error != null) ...[
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                  const SizedBox(height: 12),
                ],
                if (_readOnly)
                  _readOnlyBody()
                else
                  _editableBody(),
                if (!_readOnly) ...[
                  const SizedBox(height: 24),
                  FilledButton(
                    onPressed: _saving ? null : _save,
                    child: _saving
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white))
                        : const Text('Opslaan'),
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton(
                    onPressed: _saving ? null : _confirmDelete,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Theme.of(context).colorScheme.error,
                    ),
                    child: const Text('Verwijderen'),
                  ),
                ],
              ],
            ),
    );
  }

  Widget _readOnlyBody() {
    final person = _person;
    final anchor = _anchorDate ?? widget.task.date;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(_titleCtrl.text,
            style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 16),
        if (_descCtrl.text.isNotEmpty) ...[
          Text(_descCtrl.text),
          const SizedBox(height: 16),
        ],
        _infoRow('Datum', _fmtDate(widget.task.date)),
        _infoRow('Herhaling', _repeat.summary(anchor)),
        if (person != null)
          _infoRow('Gebruiker', person.name),
        if (widget.task.completed)
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text('Afgerond op deze dag',
                style: TextStyle(fontStyle: FontStyle.italic)),
          ),
      ],
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(label,
                style: const TextStyle(fontWeight: FontWeight.w600)),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  Widget _editableBody() {
    final anchor = _anchorDate ?? widget.task.date;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextFormField(
          controller: _titleCtrl,
          decoration: const InputDecoration(
            labelText: 'Titel',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _descCtrl,
          decoration: const InputDecoration(
            labelText: 'Beschrijving',
            border: OutlineInputBorder(),
          ),
          maxLines: 3,
        ),
        const SizedBox(height: 12),
        ListTile(
          contentPadding: EdgeInsets.zero,
          leading: const Icon(Icons.calendar_today),
          title: Text(_fmtDate(anchor)),
          onTap: () async {
            final picked = await showDatePicker(
              context: context,
              initialDate: anchor,
              firstDate: DateTime(2020),
              lastDate: DateTime(2030),
            );
            if (picked != null) setState(() => _anchorDate = picked);
          },
        ),
        RepeatSettingsField(
          anchorDate: anchor,
          value: _repeat,
          onChanged: (v) => setState(() => _repeat = v),
        ),
      ],
    );
  }

  Future<void> _save() async {
    if (_titleCtrl.text.trim().isEmpty) return;
    final id = _apiTaskId;
    if (id == null) return;
    final anchor = _anchorDate ?? widget.task.date;
    final repeatError = _repeat.validate(anchor);
    if (repeatError != null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(repeatError)));
      return;
    }
    setState(() => _saving = true);
    try {
      final data = {
        'title': _titleCtrl.text.trim(),
        'description': _descCtrl.text.trim(),
        'anchor_date': _isoDate(anchor),
        ..._repeat.toApiPayload(),
      };
      await ApiClient.instance.updateTask(id, data);
      if (mounted) {
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Taak opgeslagen')),
        );
      }
    } catch (e) {
      setState(() => _saving = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Opslaan mislukt: $e')),
        );
      }
    }
  }

  Future<void> _confirmDelete() async {
    final id = _apiTaskId;
    if (id == null) return;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Verwijderen'),
        content: const Text('Deze taak definitief verwijderen?'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Annuleren')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Verwijderen')),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() => _saving = true);
    try {
      await ApiClient.instance.deleteTask(id);
      ref.read(tasksProvider.notifier).removeTask(widget.task.id);
      if (mounted) Navigator.pop(context, true);
    } catch (e) {
      setState(() => _saving = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Verwijderen mislukt: $e')),
        );
      }
    }
  }
}
