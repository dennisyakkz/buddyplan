import 'package:flutter/material.dart';
import '../data/icon_catalog.dart';
import '../models/icon_catalog_entry.dart';
import '../ui/material_task_icon.dart';

class IconPickerField extends StatelessWidget {
  final String value;
  final ValueChanged<String> onChanged;
  final bool enabled;

  const IconPickerField({
    super.key,
    required this.value,
    required this.onChanged,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final id = MaterialTaskIcon.normalize(value);
    return FutureBuilder<List<IconCatalogEntry>>(
      future: IconCatalog.load(),
      builder: (context, snapshot) {
        final label = IconCatalog.labelFor(id, catalog: snapshot.data);
        return ListTile(
          contentPadding: EdgeInsets.zero,
          enabled: enabled,
          leading: MaterialTaskIcon(iconId: id, size: 28),
          title: const Text('Icoon'),
          subtitle: Text(label),
          trailing: enabled ? const Icon(Icons.chevron_right) : null,
          onTap: enabled ? () => _openPicker(context, id) : null,
        );
      },
    );
  }

  Future<void> _openPicker(BuildContext context, String current) async {
    final result = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => IconPickerSheet(initialId: current),
    );
    if (result != null) onChanged(result);
  }
}

class IconPickerSheet extends StatefulWidget {
  final String initialId;

  const IconPickerSheet({super.key, required this.initialId});

  @override
  State<IconPickerSheet> createState() => _IconPickerSheetState();
}

class _IconPickerSheetState extends State<IconPickerSheet> {
  final _searchCtrl = TextEditingController();
  List<IconCatalogEntry>? _catalog;
  List<IconCatalogEntry> _filtered = const [];
  String? _error;
  late String _selected;

  @override
  void initState() {
    super.initState();
    _selected = MaterialTaskIcon.normalize(widget.initialId);
    _load();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final catalog = await IconCatalog.load();
      if (!mounted) return;
      setState(() {
        _catalog = catalog;
        _applyFilter(_searchCtrl.text);
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = 'Iconen laden mislukt');
    }
  }

  void _applyFilter(String query) {
    final catalog = _catalog;
    if (catalog == null) return;
    _filtered = IconCatalog.filter(catalog, query);
  }

  @override
  Widget build(BuildContext context) {
    final height = MediaQuery.of(context).size.height * 0.75;
    final catalog = _catalog;
    final showHint = catalog != null &&
        _searchCtrl.text.trim().isEmpty &&
        catalog.length > _filtered.length;

    return SafeArea(
      child: SizedBox(
        height: height,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 8, 24, 0),
              child: Text(
                'Icoon kiezen',
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(24, 12, 24, 8),
              child: TextField(
                controller: _searchCtrl,
                autofocus: true,
                decoration: const InputDecoration(
                  hintText: 'Zoek icoon (bijv. wasmachine, kliko, voetbal)',
                  prefixIcon: Icon(Icons.search),
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
                onChanged: (q) => setState(() => _applyFilter(q)),
              ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24),
                child: Text(_error!,
                    style: TextStyle(color: Theme.of(context).colorScheme.error)),
              )
            else if (catalog == null)
              const Expanded(
                child: Center(child: CircularProgressIndicator()),
              )
            else
              Expanded(
                child: Column(
                  children: [
                    if (showHint)
                      Padding(
                        padding: const EdgeInsets.fromLTRB(24, 0, 24, 8),
                        child: Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                            'Typ om te zoeken in ${catalog.length} iconen',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ),
                      ),
                    Expanded(
                      child: _filtered.isEmpty
                          ? const Center(child: Text('Geen iconen gevonden'))
                          : GridView.builder(
                              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                              gridDelegate:
                                  const SliverGridDelegateWithFixedCrossAxisCount(
                                crossAxisCount: 4,
                                mainAxisSpacing: 8,
                                crossAxisSpacing: 8,
                                childAspectRatio: 0.85,
                              ),
                              itemCount: _filtered.length,
                              itemBuilder: (context, index) {
                                final item = _filtered[index];
                                final selected = item.id == _selected;
                                return InkWell(
                                  borderRadius: BorderRadius.circular(12),
                                  onTap: () =>
                                      Navigator.pop(context, item.id),
                                  child: Container(
                                    decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(12),
                                      border: Border.all(
                                        color: selected
                                            ? Theme.of(context)
                                                .colorScheme
                                                .primary
                                            : Theme.of(context)
                                                .colorScheme
                                                .outlineVariant,
                                        width: selected ? 2 : 1,
                                      ),
                                      color: selected
                                          ? Theme.of(context)
                                              .colorScheme
                                              .primaryContainer
                                              .withValues(alpha: 0.35)
                                          : null,
                                    ),
                                    padding: const EdgeInsets.all(6),
                                    child: Column(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        MaterialTaskIcon(
                                          iconId: item.id,
                                          size: 28,
                                        ),
                                        const SizedBox(height: 6),
                                        Text(
                                          item.label,
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          textAlign: TextAlign.center,
                                          style: Theme.of(context)
                                              .textTheme
                                              .labelSmall,
                                        ),
                                      ],
                                    ),
                                  ),
                                );
                              },
                            ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
