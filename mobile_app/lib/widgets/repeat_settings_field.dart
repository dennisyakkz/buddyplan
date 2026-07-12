import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/repeat_settings.dart';

class RepeatSettingsField extends StatelessWidget {
  final DateTime anchorDate;
  final RepeatSettings value;
  final ValueChanged<RepeatSettings> onChanged;

  const RepeatSettingsField({
    super.key,
    required this.anchorDate,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final endSummary = value.endSummary();

    return ListTile(
      contentPadding: EdgeInsets.zero,
      leading: Icon(
        value.repeatType == 'once' ? Icons.event : Icons.repeat,
        color: Theme.of(context).colorScheme.primary,
      ),
      title: Text(value.summary(anchorDate)),
      subtitle: endSummary != null ? Text(endSummary) : null,
      trailing: const Icon(Icons.chevron_right),
      onTap: () => _openPicker(context),
    );
  }

  Future<void> _openPicker(BuildContext context) async {
    final result = await showModalBottomSheet<RepeatSettings>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => RepeatSettingsPicker(
        anchorDate: anchorDate,
        initial: value,
      ),
    );
    if (result != null) onChanged(result);
  }
}

class RepeatSettingsPicker extends StatefulWidget {
  final DateTime anchorDate;
  final RepeatSettings initial;

  const RepeatSettingsPicker({
    super.key,
    required this.anchorDate,
    required this.initial,
  });

  @override
  State<RepeatSettingsPicker> createState() => _RepeatSettingsPickerState();
}

class _RepeatSettingsPickerState extends State<RepeatSettingsPicker> {
  late String _repeatType;
  late List<int> _weekdays;
  DateTime? _endDate;
  late bool _hasEndDate;
  String? _error;

  @override
  void initState() {
    super.initState();
    _repeatType = widget.initial.repeatType;
    _weekdays = List<int>.from(widget.initial.repeatWeekdays);
    _endDate = widget.initial.endDate;
    _hasEndDate = _endDate != null;
  }

  String _weeklyLabel(String base) {
    final day = weekdayFullLabels[widget.anchorDate.weekday - 1];
    return '$base op $day';
  }

  String _labelForType(String type) {
    switch (type) {
      case 'daily':
        return 'Dagelijks';
      case 'weekly':
        return _weeklyLabel('Wekelijks');
      case 'biweekly':
        return _weeklyLabel('Om de 2 weken');
      case 'weekdays':
        return 'Op bepaalde dagen';
      case 'once':
      default:
        return 'Eenmalig';
    }
  }

  void _selectType(String type) {
    setState(() {
      _repeatType = type;
      _error = null;
      if (type == 'weekdays' && _weekdays.isEmpty) {
        _weekdays = [widget.anchorDate.weekday - 1];
      }
      if (type == 'once') {
        _endDate = null;
      }
    });
  }

  void _toggleWeekday(int day) {
    setState(() {
      if (_weekdays.contains(day)) {
        _weekdays.remove(day);
      } else {
        _weekdays.add(day);
      }
      _error = null;
    });
  }

  Future<void> _pickEndDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _endDate ?? widget.anchorDate,
      firstDate: widget.anchorDate,
      lastDate: DateTime(2035),
      locale: const Locale('nl'),
    );
    if (picked != null) {
      setState(() => _endDate = picked);
    }
  }

  void _apply() {
    final settings = RepeatSettings(
      repeatType: _repeatType,
      repeatWeekdays: _weekdays,
      endDate: _hasEndDate ? _endDate : null,
    );
    final validation = settings.validate(widget.anchorDate);
    if (validation != null) {
      setState(() => _error = validation);
      return;
    }
    Navigator.pop(context, settings);
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;

    return Padding(
      padding: EdgeInsets.only(bottom: bottomInset),
      child: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Herhalen',
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 8),
              ...repeatTypeOptions.map((option) {
                final selected = _repeatType == option.$1;
                return RadioListTile<String>(
                  value: option.$1,
                  groupValue: _repeatType,
                  title: Text(_labelForType(option.$1)),
                  onChanged: (v) {
                    if (v != null) _selectType(v);
                  },
                  selected: selected,
                  contentPadding: EdgeInsets.zero,
                );
              }),
              if (_repeatType == 'weekdays') ...[
                const SizedBox(height: 4),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: List.generate(7, (day) {
                    final selected = _weekdays.contains(day);
                    return FilterChip(
                      label: Text(weekdayShortLabels[day]),
                      selected: selected,
                      onSelected: (_) => _toggleWeekday(day),
                      showCheckmark: false,
                      selectedColor:
                          Theme.of(context).colorScheme.primaryContainer,
                    );
                  }),
                ),
              ],
              if (_repeatType != 'once') ...[
                const SizedBox(height: 16),
                Text(
                  'Eindigt',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                RadioListTile<bool>(
                  value: false,
                  groupValue: _hasEndDate,
                  title: const Text('Nooit'),
                  onChanged: (_) => setState(() {
                    _hasEndDate = false;
                    _endDate = null;
                  }),
                  contentPadding: EdgeInsets.zero,
                ),
                RadioListTile<bool>(
                  value: true,
                  groupValue: _hasEndDate,
                  title: Text(
                    _endDate == null
                        ? 'Op datum'
                        : DateFormat('d MMMM yyyy', 'nl_NL')
                            .format(_endDate!),
                  ),
                  onChanged: (_) async {
                    setState(() => _hasEndDate = true);
                    if (_endDate == null) {
                      await _pickEndDate();
                    }
                  },
                  secondary: _hasEndDate
                      ? IconButton(
                          icon: const Icon(Icons.edit_calendar),
                          onPressed: _pickEndDate,
                        )
                      : null,
                  contentPadding: EdgeInsets.zero,
                ),
              ],
              if (_error != null) ...[
                const SizedBox(height: 8),
                Text(_error!, style: const TextStyle(color: Colors.red)),
              ],
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _apply,
                child: const Text('Klaar'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
