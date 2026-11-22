import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../models/ai_message.dart';
import '../../providers/ai_provider.dart';
import '../../providers/voice_provider.dart';

/// Messenger-style chat with the AI buddy (REQ-MOB-051..053, REQ-MOB-055..057).
class AiChatScreen extends ConsumerStatefulWidget {
  const AiChatScreen({super.key});

  @override
  ConsumerState<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends ConsumerState<AiChatScreen> {
  final _input = TextEditingController();
  bool _hasText = false;

  @override
  void initState() {
    super.initState();
    _input.addListener(() {
      final hasText = _input.text.trim().isNotEmpty;
      if (hasText != _hasText) setState(() => _hasText = hasText);
    });
    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(aiChatProvider.notifier).load();
    });
  }

  @override
  void deactivate() {
    ref.read(voiceProvider.notifier).stopListening();
    super.deactivate();
  }

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final text = _input.text;
    if (text.trim().isEmpty) return;
    _input.clear();
    await ref.read(aiChatProvider.notifier).send(text);
  }

  Future<void> _confirmClear() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Gesprek wissen?'),
        content: const Text(
            'Alle berichten met de AI buddy worden verwijderd, ook op je andere apparaten.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Annuleren'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Wissen'),
          ),
        ],
      ),
    );
    if (ok == true) await ref.read(aiChatProvider.notifier).clear();
  }

  /// Puts the recognised text in the text field, and shows why voice input is
  /// not possible (REQ-MOB-056).
  void _onVoice(VoiceState? previous, VoiceState next) {
    if (previous?.revision != next.revision) {
      _input.value = TextEditingValue(
        text: next.text,
        selection: TextSelection.collapsed(offset: next.text.length),
      );
    }
    if (next.message != null) {
      ScaffoldMessenger.of(context)
        ..hideCurrentSnackBar()
        ..showSnackBar(SnackBar(content: Text(next.message!)));
      ref.read(voiceProvider.notifier).clearMessage();
    }
  }

  @override
  Widget build(BuildContext context) {
    ref.listen(voiceProvider, _onVoice);
    final chat = ref.watch(aiChatProvider);
    final voice = ref.watch(voiceProvider);
    final autoSend = ref.watch(voiceAutoSendProvider);
    // Newest at the bottom: the list is reversed, so index 0 is the bottom row.
    final rows = <Widget>[
      if (chat.isSending) const _TypingBubble(),
      if (chat.failedText != null && !chat.isSending)
        _ErrorRow(
          message: chat.error ?? 'Versturen mislukt',
          onRetry: () => ref.read(aiChatProvider.notifier).retry(),
        ),
      for (final message in chat.messages.reversed) _MessageBubble(message),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('AI buddy'),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) {
              if (value == 'clear') _confirmClear();
              if (value == 'auto-send') {
                ref.read(voiceAutoSendProvider.notifier).set(!autoSend);
              }
            },
            itemBuilder: (_) => [
              CheckedPopupMenuItem(
                value: 'auto-send',
                checked: autoSend,
                child: const Text('Spraak direct versturen'),
              ),
              const PopupMenuItem(
                  value: 'clear', child: Text('Gesprek wissen')),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: chat.isLoading && chat.messages.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : rows.isEmpty
                    ? _EmptyState(error: chat.error)
                    : ListView(
                        reverse: true,
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 8),
                        children: rows,
                      ),
          ),
          _InputBar(
            controller: _input,
            canSend: _hasText && !chat.isSending,
            onSend: _send,
            showMicrophone: showMicrophone(
                hasText: _hasText, isListening: voice.isListening),
            isListening: voice.isListening,
            onMicrophone: chat.isSending
                ? null
                : () => ref.read(voiceProvider.notifier).toggle(),
          ),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  final AiMessage message;

  const _MessageBubble(this.message);

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final mine = message.isUser;
    final background =
        mine ? scheme.primaryContainer : scheme.surfaceContainerHighest;
    final foreground = mine ? scheme.onPrimaryContainer : scheme.onSurface;
    return Align(
      alignment: mine ? Alignment.centerRight : Alignment.centerLeft,
      child: ConstrainedBox(
        constraints:
            BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
        child: Container(
          margin: const EdgeInsets.symmetric(vertical: 3),
          padding: const EdgeInsets.fromLTRB(12, 8, 12, 6),
          decoration: BoxDecoration(
            color: background,
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(16),
              topRight: const Radius.circular(16),
              bottomLeft: Radius.circular(mine ? 16 : 4),
              bottomRight: Radius.circular(mine ? 4 : 16),
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              SelectableText(message.text,
                  style: TextStyle(color: foreground, fontSize: 15)),
              const SizedBox(height: 2),
              Text(
                DateFormat('HH:mm').format(message.createdAt),
                style: TextStyle(
                    color: foreground.withValues(alpha: 0.6), fontSize: 11),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Three dots that bounce in turn, like a messenger app's "is typing" (REQ-MOB-052).
class _TypingBubble extends StatefulWidget {
  const _TypingBubble();

  @override
  State<_TypingBubble> createState() => _TypingBubbleState();
}

class _TypingBubbleState extends State<_TypingBubble>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 1200),
  )..repeat();

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 3),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        decoration: BoxDecoration(
          color: scheme.surfaceContainerHighest,
          borderRadius: const BorderRadius.only(
            topLeft: Radius.circular(16),
            topRight: Radius.circular(16),
            bottomLeft: Radius.circular(4),
            bottomRight: Radius.circular(16),
          ),
        ),
        child: Semantics(
          label: 'AI buddy is aan het typen',
          child: AnimatedBuilder(
            animation: _controller,
            builder: (context, _) => Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                for (var i = 0; i < 3; i++)
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 2),
                    child: Transform.translate(
                      offset: Offset(0, -4 * _bounce(_controller.value, i)),
                      child: Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: scheme.onSurface.withValues(alpha: 0.5),
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  /// 0..1..0 for dot [index], each dot a third of the cycle later.
  double _bounce(double t, int index) {
    final phase = (t - index / 3) % 1.0;
    if (phase > 0.5) return 0;
    return phase < 0.25 ? phase * 4 : (0.5 - phase) * 4;
  }
}

class _ErrorRow extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorRow({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Align(
      alignment: Alignment.centerRight,
      child: Padding(
        padding: const EdgeInsets.only(top: 2, bottom: 6),
        child: Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          alignment: WrapAlignment.end,
          children: [
            Icon(Icons.error_outline, size: 16, color: scheme.error),
            const SizedBox(width: 4),
            Text(message, style: TextStyle(color: scheme.error, fontSize: 12)),
            TextButton(onPressed: onRetry, child: const Text('Opnieuw')),
          ],
        ),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  final String? error;

  const _EmptyState({this.error});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Text(
          error ??
              'Vraag de AI buddy iets over de agenda of de taken, of geef een opdracht, '
                  "zoals 'Zet morgen om 16:00 zwemles in mijn agenda'.",
          textAlign: TextAlign.center,
          style: TextStyle(color: Theme.of(context).hintColor),
        ),
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  final TextEditingController controller;
  final bool canSend;
  final VoidCallback onSend;
  final bool showMicrophone;
  final bool isListening;
  final VoidCallback? onMicrophone;

  const _InputBar({
    required this.controller,
    required this.canSend,
    required this.onSend,
    required this.showMicrophone,
    required this.isListening,
    required this.onMicrophone,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(8, 4, 8, 8),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                minLines: 1,
                maxLines: 5,
                maxLength: 4000,
                textCapitalization: TextCapitalization.sentences,
                readOnly: isListening,
                decoration: InputDecoration(
                  hintText: isListening ? 'Luisteren…' : 'Bericht',
                  counterText: '',
                  border: const OutlineInputBorder(
                      borderRadius: BorderRadius.all(Radius.circular(24))),
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                ),
              ),
            ),
            const SizedBox(width: 6),
            if (showMicrophone)
              _MicrophoneButton(
                  isListening: isListening, onPressed: onMicrophone)
            else
              IconButton.filled(
                onPressed: canSend ? onSend : null,
                icon: const Icon(Icons.send),
                tooltip: 'Versturen',
              ),
          ],
        ),
      ),
    );
  }
}

/// Starts voice input; while listening it pulses and shows a stop icon (REQ-MOB-056).
class _MicrophoneButton extends StatefulWidget {
  final bool isListening;
  final VoidCallback? onPressed;

  const _MicrophoneButton({required this.isListening, required this.onPressed});

  @override
  State<_MicrophoneButton> createState() => _MicrophoneButtonState();
}

class _MicrophoneButtonState extends State<_MicrophoneButton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _pulse = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 900),
  );

  @override
  void initState() {
    super.initState();
    if (widget.isListening) _pulse.repeat(reverse: true);
  }

  @override
  void didUpdateWidget(covariant _MicrophoneButton oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isListening && !_pulse.isAnimating) {
      _pulse.repeat(reverse: true);
    } else if (!widget.isListening && _pulse.isAnimating) {
      _pulse
        ..stop()
        ..value = 0;
    }
  }

  @override
  void dispose() {
    _pulse.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final button = IconButton.filled(
      onPressed: widget.onPressed,
      style: widget.isListening
          ? IconButton.styleFrom(
              backgroundColor: scheme.error, foregroundColor: scheme.onError)
          : null,
      icon: Icon(widget.isListening ? Icons.stop : Icons.mic),
      tooltip: widget.isListening ? 'Stoppen met luisteren' : 'Inspreken',
    );
    if (!widget.isListening) return button;
    return AnimatedBuilder(
      animation: _pulse,
      builder: (context, child) => DecoratedBox(
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          boxShadow: [
            BoxShadow(
              color: scheme.error.withValues(alpha: 0.35),
              blurRadius: 4 + 10 * _pulse.value,
              spreadRadius: 1 + 4 * _pulse.value,
            ),
          ],
        ),
        child: child,
      ),
      child: button,
    );
  }
}
