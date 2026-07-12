class TaskItem {
  final String id;
  final String title;
  final String description;
  final String icon;
  final int? personId;
  final DateTime date;
  bool completed;

  TaskItem({
    required this.id,
    required this.title,
    required this.description,
    required this.icon,
    required this.personId,
    required this.date,
    required this.completed,
  });

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    return TaskItem(
      id: json['id'] as String,
      title: json['title'] as String,
      description: (json['description'] as String?) ?? '',
      icon: (json['icon'] as String?) ?? 'check',
      personId: json['person_id'] as int?,
      date: DateTime.parse(json['date'] as String),
      completed: (json['completed'] as bool?) ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'description': description,
        'icon': icon,
        'person_id': personId,
        'date': date.toIso8601String().split('T').first,
        'completed': completed,
      };
}
