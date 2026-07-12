import 'package:flutter/material.dart';

/// Detects horizontal swipes to navigate between periods.
///
/// Swipe right → [onSwipeToPrevious], swipe left → [onSwipeToNext].
class SwipeNavDetector extends StatefulWidget {
  final Widget child;
  final VoidCallback? onSwipeToPrevious;
  final VoidCallback? onSwipeToNext;

  const SwipeNavDetector({
    super.key,
    required this.child,
    this.onSwipeToPrevious,
    this.onSwipeToNext,
  });

  @override
  State<SwipeNavDetector> createState() => _SwipeNavDetectorState();
}

class _SwipeNavDetectorState extends State<SwipeNavDetector> {
  static const _minDistance = 72.0;
  static const _minVelocity = 350.0;

  double _dragDistance = 0;

  void _onDragStart(DragStartDetails _) {
    _dragDistance = 0;
  }

  void _onDragUpdate(DragUpdateDetails details) {
    _dragDistance += details.delta.dx;
  }

  void _onDragEnd(DragEndDetails details) {
    final velocity = details.primaryVelocity ?? 0;
    if (_dragDistance >= _minDistance || velocity >= _minVelocity) {
      widget.onSwipeToPrevious?.call();
    } else if (_dragDistance <= -_minDistance || velocity <= -_minVelocity) {
      widget.onSwipeToNext?.call();
    }
    _dragDistance = 0;
  }

  @override
  Widget build(BuildContext context) {
    if (widget.onSwipeToPrevious == null && widget.onSwipeToNext == null) {
      return widget.child;
    }

    return GestureDetector(
      behavior: HitTestBehavior.translucent,
      onHorizontalDragStart: _onDragStart,
      onHorizontalDragUpdate: _onDragUpdate,
      onHorizontalDragEnd: _onDragEnd,
      child: widget.child,
    );
  }
}
