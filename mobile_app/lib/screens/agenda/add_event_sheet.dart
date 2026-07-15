import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/network_utils.dart';
import '../../models/repeat_settings.dart';
import '../../models/calendar_event.dart';
import '../../providers/calendar_provider.dart';
import '../../providers/persons_provider.dart';
import '../../ui/color_palette.dart';
import '../../widgets/repeat_settings_field.dart';

class AddEventSheet extends ConsumerStatefulWidget {
  final DateTime initialDate;
  final void Function(CalendarEvent) onSaved;

  const AddEventSheet(
      {super.key, required this.initialDate, required this.onSaved});

  @override
  ConsumerState<AddEventSheet> createState() => _AddEventSheetState();
}

class _AddEventSheetState extends ConsumerState<AddEventSheet> {
  final _formKey = GlobalKey<FormState>();
  final _titleCtrl = TextEditingController();
  late DateTime _date;
  TimeOfDay? _startTime;
  TimeOfDay? _endTime;
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
    super.dispose();
  }

  String _fmtDate(DateTime d) =>
      DateFormat('d MMMM yyyy', 'nl_NL').format(d);

  String _fmtTime(TimeOfDay t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  @override
  Widget build(BuildContext context) {
    final persons = ref
        .watch(personsProvider)
        .persons
        .where((p) => p.canManageAgenda)
        .toList();
    if (_personId == null && persons.isNotEmpty) {
      _personId =
          persons.firstWhere((p) => p.isMe, orElse: () => persons.first).id;
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
                Text('Nieuw agenda-item',
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
                // Date picker
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
                    );
                    if (picked != null) setState(() => _date = picked);
                  },
                ),
                // Time pickers
                Row(children: [
                  Expanded(
                    child: ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.access_time),
                      title: Text(_startTime != null
                          ? _fmtTime(_startTime!)
                          : 'Starttijd'),
                      onTap: () async {
                        final t = await showTimePicker(
                          context: context,
                          initialTime: _startTime ?? TimeOfDay.now(),
                        );
                        if (t != null) setState(() => _startTime = t);
                      },
                    ),
                  ),
                  const Text('–'),
                  Expanded(
                    child: ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text(_endTime != null
                          ? _fmtTime(_endTime!)
                          : 'Eindtijd'),
                      onTap: () async {
                        final t = await showTimePicker(
                          context: context,
                          initialTime: _endTime ??
                              (_startTime != null
                                  ? TimeOfDay(
                                      hour: (_startTime!.hour + 1) % 24,
                                      minute: _startTime!.minute)
                                  : TimeOfDay.now()),
                        );
                        if (t != null) setState(() => _endTime = t);
                      },
                    ),
                  ),
                ]),
                RepeatSettingsField(
                  anchorDate: _date,
                  value: _repeat,
                  onChanged: (v) => setState(() => _repeat = v),
                ),
                // Person picker
                if (persons.length > 1) ...[
                  DropdownButtonFormField<int>(
                    decoration: const InputDecoration(
                        labelText: 'Kalender',
                        border: OutlineInputBorder()),
                    value: _personId,
                    items: persons
                        .map((p) => DropdownMenuItem(
                              value: p.id,
                              child: Row(children: [
                                CircleAvatar(
                                    backgroundColor: ColorPalette.dotColor(
                                        context, p.profileColor),
                                    radius: 6),
                                const SizedBox(width: 8),
                                Text(p.isMe ? 'Mijn kalender' : p.name),
                              ]),
                            ))
                        .toList(),
                    onChanged: (v) => setState(() => _personId = v),
                  ),
                ],
                if (persons.isEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Je hebt geen rechten om agenda-items toe te voegen.',
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
                  onPressed: (_saving || persons.isEmpty) ? null : _save,
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
      setState(() => _error = 'Kies een kalender');
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
        'person_id': _personId,
        'title': _titleCtrl.text.trim(),
        'anchor_date': _isoDate(_date),
        if (_startTime != null) 'start_time': _fmtTime(_startTime!),
        if (_endTime != null) 'end_time': _fmtTime(_endTime!),
        ..._repeat.toApiPayload(),
      };
      final localId = -DateTime.now().millisecondsSinceEpoch;
      final event = CalendarEvent(
        id: localId,
        title: _titleCtrl.text.trim(),
        personId: _personId!,
        date: _date,
        startTime: _startTime != null ? _fmtTime(_startTime!) : null,
        endTime: _endTime != null ? _fmtTime(_endTime!) : null,
      );
      await ref.read(calendarProvider.notifier).addEventWithPayload(
            apiPayload: data,
            optimistic: event,
          );
      widget.onSaved(event);
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
