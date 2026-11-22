import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../core/api_client.dart';
import '../core/network_utils.dart';
import '../models/ai_message.dart';
import 'auth_provider.dart';

/// The calls the AI buddy screen needs; replaced by a fake in tests.
abstract class AiChatApi {
  Future<bool> configured();
  Future<List<AiMessage>> messages();
  Future<({AiMessage userMessage, AiMessage reply})> send(String text);
  Future<void> clear();
}

class _HttpAiChatApi implements AiChatApi {
  ApiClient get _api => ApiClient.instance;

  @override
  Future<bool> configured() => _api.fetchAiConfigured();

  @override
  Future<List<AiMessage>> messages() async => (await _api.fetchAiMessages())
      .map((m) => AiMessage.fromJson(m as Map<String, dynamic>))
      .toList();

  @override
  Future<({AiMessage userMessage, AiMessage reply})> send(String text) async {
    final data = await _api.sendAiMessage(text);
    return (
      userMessage:
          AiMessage.fromJson(data['user_message'] as Map<String, dynamic>),
      reply: AiMessage.fromJson(data['reply'] as Map<String, dynamic>),
    );
  }

  @override
  Future<void> clear() => _api.clearAiMessages();
}

final aiChatApiProvider = Provider<AiChatApi>((ref) => _HttpAiChatApi());

/// Whether the backend has the AI buddy configured (REQ-MOB-050). Stays at the
/// last known value when the check fails, so a network hiccup does not hide the tab.
class AiStatusNotifier extends Notifier<bool> {
  @override
  bool build() => false;

  Future<void> refresh() async {
    try {
      state = await ref.read(aiChatApiProvider).configured();
    } catch (err) {
      if (isAuthError(err)) {
        ref.read(authProvider.notifier).handleSessionExpired();
      }
    }
  }
}

final aiConfiguredProvider =
    NotifierProvider<AiStatusNotifier, bool>(AiStatusNotifier.new);

/// Bumped after each AI buddy answer; the agenda and task screens reload on it (REQ-MOB-054).
class DataRefreshNotifier extends Notifier<int> {
  @override
  int build() => 0;

  void bump() => state++;
}

final dataRefreshProvider =
    NotifierProvider<DataRefreshNotifier, int>(DataRefreshNotifier.new);

class AiChatState {
  final List<AiMessage> messages;
  final bool isLoading;

  /// Waiting for the AI buddy's answer: show the typing indicator (REQ-MOB-052).
  final bool isSending;

  /// The text of a message that could not be answered, with the error (REQ-MOB-053).
  final String? failedText;
  final String? error;

  const AiChatState({
    this.messages = const [],
    this.isLoading = false,
    this.isSending = false,
    this.failedText,
    this.error,
  });

  AiChatState copyWith({
    List<AiMessage>? messages,
    bool? isLoading,
    bool? isSending,
    String? failedText,
    String? error,
    bool clearFailure = false,
  }) =>
      AiChatState(
        messages: messages ?? this.messages,
        isLoading: isLoading ?? this.isLoading,
        isSending: isSending ?? this.isSending,
        failedText: clearFailure ? null : failedText ?? this.failedText,
        error: clearFailure ? null : error ?? this.error,
      );
}

class AiChatNotifier extends Notifier<AiChatState> {
  int _localIds = -1;

  @override
  AiChatState build() => const AiChatState();

  AiChatApi get _api => ref.read(aiChatApiProvider);

  Future<void> load() async {
    state = state.copyWith(isLoading: true);
    try {
      final messages = await _api.messages();
      state = state.copyWith(messages: messages, isLoading: false);
    } catch (err) {
      if (isAuthError(err)) {
        ref.read(authProvider.notifier).handleSessionExpired();
        return;
      }
      state =
          state.copyWith(isLoading: false, error: friendlyErrorMessage(err));
    }
  }

  Future<void> send(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || state.isSending) return;
    final isRetry = state.failedText == trimmed;
    final pending = AiMessage(
      id: _localIds--,
      isUser: true,
      text: trimmed,
      createdAt: DateTime.now(),
    );
    state = AiChatState(
      // A retry already shows the message; the backend reuses it as well.
      messages: isRetry ? state.messages : [...state.messages, pending],
      isSending: true,
    );
    try {
      final result = await _api.send(trimmed);
      final withoutPending = state.messages
          .where((m) => !(m.id < 0 && m.isUser && m.text == trimmed))
          .toList();
      state = AiChatState(
        messages: [...withoutPending, result.userMessage, result.reply],
      );
      ref.read(dataRefreshProvider.notifier).bump();
    } catch (err) {
      if (isAuthError(err)) {
        state = state.copyWith(isSending: false);
        ref.read(authProvider.notifier).handleSessionExpired();
        return;
      }
      state = state.copyWith(
        isSending: false,
        failedText: trimmed,
        error: friendlyErrorMessage(err),
      );
    }
  }

  Future<void> retry() async {
    final text = state.failedText;
    if (text != null) await send(text);
  }

  Future<void> clear() async {
    try {
      await _api.clear();
      state = const AiChatState();
    } catch (err) {
      state = state.copyWith(error: friendlyErrorMessage(err));
    }
  }
}

final aiChatProvider =
    NotifierProvider<AiChatNotifier, AiChatState>(AiChatNotifier.new);

/// Tabs of the bottom navigation: the AI buddy only while configured (REQ-MOB-050).
int tabCount({required bool aiConfigured}) => aiConfigured ? 3 : 2;

/// The selected tab after the AI buddy tab appeared or disappeared.
int clampTab(int index, {required bool aiConfigured}) =>
    index < tabCount(aiConfigured: aiConfigured) ? index : 0;
