import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_recognition_error.dart';
import 'package:speech_to_text/speech_to_text.dart';
import '../core/preferences.dart';
import 'ai_provider.dart';

/// Whether speech recognition can be used on this phone (REQ-MOB-056).
enum SpeechAvailability { ready, noPermission, unavailable }

/// The phone's speech recognition; replaced by a fake in tests.
abstract class SpeechService {
  /// Asks for microphone permission the first time.
  Future<SpeechAvailability> init();

  /// Listens in Dutch. [onPartial] gets the text so far; [onDone] is called once
  /// with the final text (possibly empty) when recognition stops.
  Future<void> start({
    required void Function(String text) onPartial,
    required void Function(String text) onDone,
  });

  Future<void> stop();
}

class _DeviceSpeechService implements SpeechService {
  final _speech = SpeechToText();
  void Function(String)? _onDone;
  String _lastWords = '';

  @override
  Future<SpeechAvailability> init() async {
    final ok = await _speech.initialize(
      onStatus: (status) {
        if (status == SpeechToText.doneStatus ||
            status == SpeechToText.notListeningStatus) {
          _finish();
        }
      },
      onError: (SpeechRecognitionError _) => _finish(),
      // Bluetooth headsets need an extra runtime permission; the phone's microphone is enough.
      options: [SpeechToText.androidNoBluetooth],
    );
    if (ok) return SpeechAvailability.ready;
    return await _speech.hasPermission
        ? SpeechAvailability.unavailable
        : SpeechAvailability.noPermission;
  }

  @override
  Future<void> start({
    required void Function(String text) onPartial,
    required void Function(String text) onDone,
  }) async {
    _lastWords = '';
    _onDone = onDone;
    final locale = await _dutchLocale();
    await _speech.listen(
      onResult: (result) {
        _lastWords = result.recognizedWords;
        if (result.finalResult) {
          _finish();
        } else {
          onPartial(_lastWords);
        }
      },
      listenOptions: SpeechListenOptions(
        localeId: locale,
        partialResults: true,
        listenMode: ListenMode.dictation,
        pauseFor: const Duration(seconds: 3),
        listenFor: const Duration(minutes: 1),
        cancelOnError: true,
        autoPunctuation: true,
      ),
    );
  }

  Future<String?> _dutchLocale() async {
    final locales = await _speech.locales();
    for (final id in ['nl_NL', 'nl-NL']) {
      if (locales.any((l) => l.localeId == id)) return id;
    }
    final dutch = locales.where((l) => l.localeId.startsWith('nl'));
    return dutch.isEmpty ? 'nl_NL' : dutch.first.localeId;
  }

  void _finish() {
    final done = _onDone;
    _onDone = null;
    done?.call(_lastWords);
  }

  @override
  Future<void> stop() => _speech.stop();
}

final speechServiceProvider =
    Provider<SpeechService>((ref) => _DeviceSpeechService());

/// Where the 'Spraak direct versturen' setting is stored; replaced in tests (REQ-MOB-057).
abstract class VoiceSettingsStore {
  bool get autoSend;
  Future<void> setAutoSend(bool value);
}

class _PrefsVoiceSettingsStore implements VoiceSettingsStore {
  @override
  bool get autoSend => AppPreferences.voiceAutoSend;

  @override
  Future<void> setAutoSend(bool value) =>
      AppPreferences.setVoiceAutoSend(value);
}

final voiceSettingsStoreProvider =
    Provider<VoiceSettingsStore>((ref) => _PrefsVoiceSettingsStore());

/// 'Spraak direct versturen', off by default and kept on the device (REQ-MOB-057).
class VoiceAutoSendNotifier extends Notifier<bool> {
  @override
  bool build() => ref.read(voiceSettingsStoreProvider).autoSend;

  Future<void> set(bool value) async {
    state = value;
    await ref.read(voiceSettingsStoreProvider).setAutoSend(value);
  }
}

final voiceAutoSendProvider =
    NotifierProvider<VoiceAutoSendNotifier, bool>(VoiceAutoSendNotifier.new);

const voiceNoPermissionMessage =
    'Geef de app toegang tot de microfoon om in te spreken';
const voiceUnavailableMessage =
    'Spraakherkenning is niet beschikbaar op dit toestel';

class VoiceState {
  final bool isListening;

  /// The recognised text so far; the chat screen puts it in the text field.
  final String text;

  /// Increases with every change of [text], so the screen also notices an
  /// unchanged text (for example two empty results in a row).
  final int revision;

  /// A Dutch message when speech recognition cannot be used.
  final String? message;

  const VoiceState({
    this.isListening = false,
    this.text = '',
    this.revision = 0,
    this.message,
  });
}

/// Voice input for the AI buddy chat (REQ-MOB-056, REQ-MOB-057).
class VoiceNotifier extends Notifier<VoiceState> {
  @override
  VoiceState build() => const VoiceState();

  SpeechService get _speech => ref.read(speechServiceProvider);

  /// The microphone button: starts listening, or stops when already listening.
  Future<void> toggle() async {
    if (state.isListening) {
      await _speech.stop();
      return;
    }
    if (ref.read(aiChatProvider).isSending) return;
    final availability = await _speech.init();
    if (availability != SpeechAvailability.ready) {
      state = VoiceState(
        revision: state.revision,
        message: availability == SpeechAvailability.noPermission
            ? voiceNoPermissionMessage
            : voiceUnavailableMessage,
      );
      return;
    }
    state = VoiceState(isListening: true, revision: state.revision + 1);
    await _speech.start(onPartial: _partial, onDone: _done);
  }

  void _partial(String text) {
    if (!state.isListening) return;
    state =
        VoiceState(isListening: true, text: text, revision: state.revision + 1);
  }

  void _done(String text) {
    final finalText = text.trim();
    if (finalText.isNotEmpty && ref.read(voiceAutoSendProvider)) {
      state = VoiceState(revision: state.revision + 1);
      ref.read(aiChatProvider.notifier).send(finalText);
      return;
    }
    state = VoiceState(text: finalText, revision: state.revision + 1);
  }

  /// Leaving the chat stops listening.
  Future<void> stopListening() async {
    if (state.isListening) await _speech.stop();
  }

  /// The message was shown; don't show it again.
  void clearMessage() {
    if (state.message != null) {
      state = VoiceState(
          isListening: state.isListening,
          text: state.text,
          revision: state.revision);
    }
  }
}

final voiceProvider =
    NotifierProvider<VoiceNotifier, VoiceState>(VoiceNotifier.new);

/// The microphone replaces the send button while the field is empty, and stays
/// while listening so that it can be tapped to stop (REQ-MOB-056).
bool showMicrophone({required bool hasText, required bool isListening}) =>
    isListening || !hasText;
