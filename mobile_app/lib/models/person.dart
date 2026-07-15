class Person {
  final int id;
  final String name;
  final bool isMe;
  final String profileColor;
  final bool canManageAgenda;

  const Person({
    required this.id,
    required this.name,
    required this.isMe,
    required this.profileColor,
    this.canManageAgenda = false,
  });

  factory Person.fromJson(Map<String, dynamic> json) {
    return Person(
      id: json['id'] as int,
      name: json['name'] as String,
      isMe: (json['is_me'] as bool?) ?? false,
      profileColor: (json['profile_color'] as String?) ?? 'teal',
      canManageAgenda: (json['can_manage_agenda'] as bool?) ?? false,
    );
  }
}
