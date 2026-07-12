import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../core/api_client.dart';
import '../../core/network_utils.dart';
import '../../models/agenda_item_detail.dart';
import '../../models/calendar_event.dart';
import '../../models/person.dart';
import '../../models/repeat_settings.dart';
import '../../providers/calendar_provider.dart';
import '../../providers/persons_provider.dart';
import '../../widgets/repeat_settings_field.dart';

class EventDetailScreen extends ConsumerStatefulWidget {
  final CalendarEvent listEvent;
  final bool canManage;

  const EventDetailScreen({
    super.key,
    required this.listEvent,
    required this.canManage,
  });

  @override
  ConsumerState<EventDetailScreen> createState() => _EventDetailScreenState();
}

class _EventDetailScreenState extends ConsumerState<EventDetailScreen> {
  AgendaItemDetail? _detail;
  bool _loading = true;
  String? _error;

  final _titleCtrl = TextEditingController();
  DateTime? _anchorDate;
  TimeOfDay? _startTime;
  TimeOfDay? _endTime;
  RepeatSettings _repeat = const RepeatSettings();
  bool _saving = false;

  bool get _readOnly {
    if (widget.listEvent.id < 0) return true;
    if (_detail != null) return _detail!.isReadOnly || !widget.canManage;
    return widget.listEvent.isFeedSynced || !widget.canManage;
  }

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  @override
  void dispose() {
    _titleCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadDetail() async {
    if (widget.listEvent.id < 0) {
      setState(() {
        _loading = false;
        _titleCtrl.text = widget.listEvent.title;
      });
      return;
    }
    try {
      final raw =
          await ApiClient.instance.fetchCalendarEventDetail(widget.listEvent.id);
      final detail = AgendaItemDetail.fromJson(raw);
      setState(() {
        _detail = detail;
        _titleCtrl.text = detail.title;
        _anchorDate = detail.anchorDate ?? widget.listEvent.date;
        _startTime = _parseTime(detail.startTime);
        _endTime = _parseTime(detail.endTime);
        _repeat = RepeatSettings.fromApi(raw);
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _error = isNetworkError(e) ? 'Kon item niet laden' : '$e';
        _titleCtrl.text = widget.listEvent.title;
      });
    }
  }

  TimeOfDay? _parseTime(String? value) {
    if (value == null || value.isEmpty) return null;
    final parts = value.split(':');
    if (parts.length != 2) return null;
    final h = int.tryParse(parts[0]);
    final m = int.tryParse(parts[1]);
    if (h == null || m == null) return null;
    return TimeOfDay(hour: h, minute: m);
  }

  String _fmtDate(DateTime d) =>
      DateFormat('d MMMM yyyy', 'nl_NL').format(d);

  String _fmtTime(TimeOfDay t) =>
      '${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';

  String _isoDate(DateTime d) =>
      '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

  Person? _person(List<Person> persons) {
    final id = _detail?.personId ?? widget.listEvent.personId;
    for (final p in persons) {
      if (p.id == id) return p;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final persons = ref.watch(personsProvider).persons;
    final person = _person(persons);

    return Scaffold(
      appBar: AppBar(
        title: Text(_readOnly ? 'Agenda-item' : 'Agenda-item bewerken'),
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
                  _readOnlyBody(person)
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

  Widget _readOnlyBody(Person? person) {
    final detail = _detail;
    final occurrence = widget.listEvent.date;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(_titleCtrl.text,
            style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 16),
        _infoRow('Datum', _fmtDate(occurrence)),
        if (widget.listEvent.startTime != null)
          _infoRow('Starttijd', widget.listEvent.startTime!),
        if (widget.listEvent.endTime != null)
          _infoRow('Eindtijd', widget.listEvent.endTime!),
        if (person != null)
          _infoRow('Kalender', person.isMe ? 'Mijn kalender' : person.name),
        if (detail != null) ...[
          _infoRow('Herhaling',
              RepeatSettings.fromApi({
                'repeat_type': detail.repeatType,
                'repeat_weekdays': detail.repeatWeekdays,
                'end_date': detail.endDate?.toIso8601String().split('T').first,
              }).summary(detail.anchorDate ?? occurrence)),
          _infoRow('Bron', detail.sourceLabel),
        ],
        if (detail?.isReadOnly == true || widget.listEvent.isFeedSynced)
          Padding(
            padding: const EdgeInsets.only(top: 16),
            child: Text(
              'Dit item komt uit een externe kalender en kan niet worden bewerkt.',
              style: TextStyle(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
            ),
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
    final anchor = _anchorDate ?? widget.listEvent.date;
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
        Row(children: [
          Expanded(
            child: ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.access_time),
              title: Text(
                  _startTime != null ? _fmtTime(_startTime!) : 'Starttijd'),
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
              title:
                  Text(_endTime != null ? _fmtTime(_endTime!) : 'Eindtijd'),
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
          anchorDate: anchor,
          value: _repeat,
          onChanged: (v) => setState(() => _repeat = v),
        ),
      ],
    );
  }

  Future<void> _save() async {
    if (_titleCtrl.text.trim().isEmpty) return;
    final anchor = _anchorDate ?? widget.listEvent.date;
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
        'anchor_date': _isoDate(anchor),
        if (_startTime != null) 'start_time': _fmtTime(_startTime!),
        if (_endTime != null) 'end_time': _fmtTime(_endTime!),
        ..._repeat.toApiPayload(),
      };
      await ApiClient.instance
          .updateCalendarEvent(widget.listEvent.id, data);
      ref.read(calendarProvider.notifier).removeEvent(widget.listEvent.id);
      if (mounted) {
        Navigator.pop(context, true);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Agenda-item opgeslagen')),
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
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Verwijderen'),
        content: const Text('Dit agenda-item definitief verwijderen?'),
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
      await ApiClient.instance.deleteCalendarEvent(widget.listEvent.id);
      ref.read(calendarProvider.notifier).removeEvent(widget.listEvent.id);
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
