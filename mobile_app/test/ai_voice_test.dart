// REQ-MOB-056, REQ-MOB-057: voice input in the AI buddy chat, with a fake speech service.
import 'package:buddyplan_mobile/models/ai_message.dart';
import 'package:buddyplan_mobile/providers/ai_provider.dart';
import 'package:buddyplan_mobile/providers/voice_provider.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeSpeech implements SpeechService {
  SpeechAvailability availability = SpeechAvailability.ready;
  int starts = 0;
  void Function(String)? _onPartial;
  void Function(String)? _onDone;
  String _last = '';

  @override
  Future<SpeechAvailability> init() async => availability;

  @override
  Future<void> start({
    required void Function(String text) onPartial,
    required void Function(String text) onDone,
  }) async {
    starts++;
    _last = '';
    _onPartial = onPartial;
    _onDone = onDone;
  }

  void speak(String text) {
    _last = text;
    _onPartial?.call(text);
  }

  /// Recognition stops by itself after a pause.
  void pause() {
    final done = _onDone;
    _onDone = null;
    done?.call(_last);
  }

  @override
  Future<void> stop() async => pause();
}

class FakeChatApi implements AiChatApi {
  final List<String> sent = [];
  bool hold = false;

  @override
  Future<bool> configured() async => true;

  @override
  Future<List<AiMessage>> messages() async => [];

  @override
  Future<({AiMessage userMessage, AiMessage reply})> send(String text) async {
    sent.add(text);
    while (hold) {
      await Future<void>.delayed(const Duration(milliseconds: 1));
    }
    final at = DateTime(2026, 11, 22, 9, 30);
    return (
      userMessage: AiMessage(id: 1, isUser: true, text: text, createdAt: at),
      reply: AiMessage(id: 2, isUser: false, text: 'Ok', createdAt: at),
    );
  }

  @override
  Future<void> clear() async {}
}

class MemoryVoiceSettings implements VoiceSettingsStore {
  bool stored = false;

  @override
  bool get autoSend => stored;

  @override
  Future<void> setAutoSend(bool value) async => stored = value;
}

void main() {
  late FakeSpeech speech;
  late FakeChatApi api;
  late MemoryVoiceSettings settings;
  late ProviderContainer container;

  ProviderContainer newContainer() => ProviderContainer(overrides: [
        speechServiceProvider.overrideWithValue(speech),
        aiChatApiProvider.overrideWithValue(api),
        voiceSettingsStoreProvider.overrideWithValue(settings),
      ]);

  setUp(() {
    speech = FakeSpeech();
    api = FakeChatApi();
    settings = MemoryVoiceSettings();
    container = newContainer();
  });
  tearDown(() => container.dispose());

  VoiceState voice() => container.read(voiceProvider);
  VoiceNotifier notifier() => container.read(voiceProvider.notifier);

  group('Voice input (REQ-MOB-056)', () {
    test('microphone only on an empty field', () async {
      expect(showMicrophone(hasText: false, isListening: false), isTrue);
      expect(showMicrophone(hasText: true, isListening: false), isFalse);
      // While listening the text fills the field, but the button stays to stop.
      expect(showMicrophone(hasText: true, isListening: true), isTrue);

      // Not while an answer is awaited (REQ-MOB-052).
      api.hold = true;
      final sending = container.read(aiChatProvider.notifier).send('Hoi');
      await notifier().toggle();
      expect(speech.starts, 0);
      expect(voice().isListening, isFalse);
      api.hold = false;
      await sending;
    });

    test('partial results fill the field', () async {
      await notifier().toggle();
      expect(voice().isListening, isTrue);
      speech.speak('Heb ik');
      expect(voice().text, 'Heb ik');
      speech.speak('Heb ik deze week training');
      expect(voice().text, 'Heb ik deze week training');
      expect(voice().isListening, isTrue);
    });

    test('final text is kept and not sent', () async {
      await notifier().toggle();
      speech.speak('Zet morgen zwemles erin ');
      speech.pause();
      expect(voice().isListening, isFalse);
      expect(voice().text, 'Zet morgen zwemles erin');
      expect(api.sent, isEmpty);

      // Tapping the button again while listening stops it.
      await notifier().toggle();
      speech.speak('Nog iets');
      await notifier().toggle();
      expect(voice().isListening, isFalse);
      expect(voice().text, 'Nog iets');
      expect(api.sent, isEmpty);
    });

    test('nothing recognised leaves the field empty', () async {
      await notifier().toggle();
      final before = voice().revision;
      speech.pause();
      expect(voice().isListening, isFalse);
      expect(voice().text, '');
      expect(voice().revision, greaterThan(before));
    });

    test('refused permission shows a message', () async {
      speech.availability = SpeechAvailability.noPermission;
      await notifier().toggle();
      expect(voice().isListening, isFalse);
      expect(voice().message,
          'Geef de app toegang tot de microfoon om in te spreken');
      notifier().clearMessage();
      expect(voice().message, isNull);
    });

    test('no speech recognition shows a message', () async {
      speech.availability = SpeechAvailability.unavailable;
      await notifier().toggle();
      expect(speech.starts, 0);
      expect(voice().message,
          'Spraakherkenning is niet beschikbaar op dit toestel');
    });
  });

  group('Send voice messages automatically (REQ-MOB-057)', () {
    test('auto-send is off by default and is stored', () async {
      expect(container.read(voiceAutoSendProvider), isFalse);
      await container.read(voiceAutoSendProvider.notifier).set(true);
      expect(settings.stored, isTrue);

      // A restart reads the stored setting.
      container.dispose();
      container = newContainer();
      expect(container.read(voiceAutoSendProvider), isTrue);
    });

    test('auto-send sends the final text', () async {
      await container.read(voiceAutoSendProvider.notifier).set(true);
      await notifier().toggle();
      speech.speak('Heb ik deze week training?');
      expect(api.sent, isEmpty); // not while still speaking
      speech.pause();
      await Future<void>.delayed(Duration.zero);
      expect(api.sent, ['Heb ik deze week training?']);
      expect(voice().text, '');
    });

    test('auto-send with nothing recognised sends nothing', () async {
      await container.read(voiceAutoSendProvider.notifier).set(true);
      await notifier().toggle();
      speech.speak('   ');
      speech.pause();
      await Future<void>.delayed(Duration.zero);
      expect(api.sent, isEmpty);
      expect(voice().text, '');
    });
  });
}
