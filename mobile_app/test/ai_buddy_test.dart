// REQ-MOB-050..055: AI buddy chat logic, with a fake backend.
import 'package:buddyplan_mobile/models/ai_message.dart';
import 'package:buddyplan_mobile/providers/ai_provider.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

AiMessage msg(int id, bool isUser, String text) => AiMessage(
    id: id,
    isUser: isUser,
    text: text,
    createdAt: DateTime(2026, 11, 22, 9, 30));

class FakeAiChatApi implements AiChatApi {
  bool isConfigured = true;
  bool failNext = false;
  final List<AiMessage> stored = [];
  final List<String> sent = [];
  int _ids = 1;

  @override
  Future<bool> configured() async => isConfigured;

  @override
  Future<List<AiMessage>> messages() async => List.of(stored);

  @override
  Future<({AiMessage userMessage, AiMessage reply})> send(String text) async {
    sent.add(text);
    if (failNext) {
      failNext = false;
      throw DioException(
        requestOptions: RequestOptions(path: '/api/ai/messages'),
        type: DioExceptionType.connectionError,
      );
    }
    final user = msg(_ids++, true, text);
    final reply = msg(_ids++, false, 'Antwoord op: $text');
    stored.addAll([user, reply]);
    return (userMessage: user, reply: reply);
  }

  @override
  Future<void> clear() async => stored.clear();
}

void main() {
  late FakeAiChatApi api;
  late ProviderContainer container;

  setUp(() {
    api = FakeAiChatApi();
    container = ProviderContainer(
        overrides: [aiChatApiProvider.overrideWithValue(api)]);
  });
  tearDown(() => container.dispose());

  AiChatState chat() => container.read(aiChatProvider);
  AiChatNotifier notifier() => container.read(aiChatProvider.notifier);

  group('AI buddy tab (REQ-MOB-050)', () {
    test('only shown while the backend has the AI buddy configured', () async {
      expect(container.read(aiConfiguredProvider), isFalse);
      await container.read(aiConfiguredProvider.notifier).refresh();
      expect(container.read(aiConfiguredProvider), isTrue);
      expect(tabCount(aiConfigured: true), 3);

      api.isConfigured = false;
      await container.read(aiConfiguredProvider.notifier).refresh();
      expect(container.read(aiConfiguredProvider), isFalse);
      expect(tabCount(aiConfigured: false), 2);
    });

    test('an open AI buddy tab falls back to Agenda when it disappears', () {
      expect(clampTab(2, aiConfigured: true), 2);
      expect(clampTab(2, aiConfigured: false), 0);
      expect(clampTab(1, aiConfigured: false), 1);
    });
  });

  group('chat (REQ-MOB-051, REQ-MOB-052)', () {
    test('loads the conversation from the backend', () async {
      api.stored.addAll([msg(1, true, 'Hoi'), msg(2, false, 'Hallo!')]);
      await notifier().load();
      expect(chat().messages.map((m) => m.text), ['Hoi', 'Hallo!']);
      expect(chat().isLoading, isFalse);
    });

    test('shows the message and the typing state while waiting', () async {
      final sending = notifier().send('Wat staat er morgen?');
      expect(chat().isSending, isTrue);
      expect(chat().messages.single.text, 'Wat staat er morgen?');
      await sending;
      expect(chat().isSending, isFalse);
      expect(chat().messages.map((m) => m.text),
          ['Wat staat er morgen?', 'Antwoord op: Wat staat er morgen?']);
      expect(chat().messages.every((m) => m.id > 0), isTrue);
    });

    test('parses the backend message format', () {
      final m = AiMessage.fromJson({
        'id': 7,
        'role': 'assistant',
        'text': 'Gedaan',
        'created_at': '2026-11-22T08:30:00+00:00',
      });
      expect(m.isUser, isFalse);
      expect(m.createdAt, DateTime.utc(2026, 11, 22, 8, 30).toLocal());
    });
  });

  group('errors and offline (REQ-MOB-053)', () {
    test('a failed message shows the error and can be sent again', () async {
      api.failNext = true;
      await notifier().send('Zet zwemles erin');
      expect(chat().failedText, 'Zet zwemles erin');
      expect(chat().error, contains('Geen verbinding'));
      expect(chat().messages.single.text, 'Zet zwemles erin');

      await notifier().retry();
      expect(api.sent, ['Zet zwemles erin', 'Zet zwemles erin']);
      expect(chat().failedText, isNull);
      expect(chat().messages.map((m) => m.text),
          ['Zet zwemles erin', 'Antwoord op: Zet zwemles erin']);
    });
  });

  group('refresh and clear (REQ-MOB-054, REQ-MOB-055)', () {
    test('every answer asks the agenda and task screens to reload', () async {
      expect(container.read(dataRefreshProvider), 0);
      await notifier().send('Een');
      await notifier().send('Twee');
      expect(container.read(dataRefreshProvider), 2);
    });

    test('a failed message does not trigger a reload', () async {
      api.failNext = true;
      await notifier().send('Een');
      expect(container.read(dataRefreshProvider), 0);
    });

    test('clearing empties the conversation on the backend', () async {
      await notifier().send('Een');
      await notifier().clear();
      expect(chat().messages, isEmpty);
      expect(api.stored, isEmpty);
    });
  });
}
