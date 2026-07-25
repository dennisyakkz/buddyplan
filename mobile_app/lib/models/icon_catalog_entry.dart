class IconCatalogEntry {
  final String id;
  final String name;
  final String label;
  final List<String> terms;

  const IconCatalogEntry({
    required this.id,
    required this.name,
    required this.label,
    required this.terms,
  });

  factory IconCatalogEntry.fromJson(Map<String, dynamic> json) {
    final rawTerms = json['terms'];
    return IconCatalogEntry(
      id: json['id'] as String,
      name: json['name'] as String? ?? '',
      label: json['label'] as String? ?? '',
      terms: rawTerms is List
          ? rawTerms.map((e) => e.toString()).toList()
          : const [],
    );
  }

  String get searchText =>
      ([label, name, ...terms].join(' ')).toLowerCase();
}
