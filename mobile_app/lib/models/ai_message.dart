/// One message in the conversation with the AI buddy (REQ-BE-087).
class AiMessage {
  final int id;
  final bool isUser;
  final String text;
  final DateTime createdAt;

  const AiMessage({
    required this.id,
    required this.isUser,
    required this.text,
    required this.createdAt,
  });

  factory AiMessage.fromJson(Map<String, dynamic> json) {
    final created = DateTime.tryParse(json['created_at'] as String? ?? '');
    return AiMessage(
      id: json['id'] as int,
      isUser: json['role'] == 'user',
      text: json['text'] as String? ?? '',
      createdAt: (created ?? DateTime.now()).toLocal(),
    );
  }
}
