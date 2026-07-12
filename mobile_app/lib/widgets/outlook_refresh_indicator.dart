import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Pull-to-refresh with a refresh icon (Outlook-style).
class OutlookRefreshIndicator extends StatefulWidget {
  final Future<void> Function() onRefresh;
  final Widget child;

  const OutlookRefreshIndicator({
    super.key,
    required this.onRefresh,
    required this.child,
  });

  @override
  State<OutlookRefreshIndicator> createState() =>
      _OutlookRefreshIndicatorState();
}

class _OutlookRefreshIndicatorState extends State<OutlookRefreshIndicator>
    with SingleTickerProviderStateMixin {
  RefreshIndicatorStatus? _status;
  late final AnimationController _spinController;

  @override
  void initState() {
    super.initState();
    _spinController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
  }

  @override
  void dispose() {
    _spinController.dispose();
    super.dispose();
  }

  void _onStatusChange(RefreshIndicatorStatus? status) {
    setState(() => _status = status);
    if (status == RefreshIndicatorStatus.refresh) {
      _spinController.repeat();
    } else if (status == RefreshIndicatorStatus.done ||
        status == RefreshIndicatorStatus.canceled ||
        status == null) {
      _spinController
        ..stop()
        ..reset();
    }
  }

  bool get _showIcon =>
      _status == RefreshIndicatorStatus.drag ||
      _status == RefreshIndicatorStatus.armed ||
      _status == RefreshIndicatorStatus.snap ||
      _status == RefreshIndicatorStatus.refresh;

  double get _pullRotation {
    switch (_status) {
      case RefreshIndicatorStatus.armed:
      case RefreshIndicatorStatus.snap:
        return math.pi * 1.5;
      case RefreshIndicatorStatus.drag:
        return math.pi * 0.75;
      default:
        return 0;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme.primary;

    return Stack(
      clipBehavior: Clip.none,
      children: [
        RefreshIndicator.noSpinner(
          onRefresh: widget.onRefresh,
          onStatusChange: _onStatusChange,
          child: widget.child,
        ),
        if (_showIcon)
          Positioned(
            top: 12,
            left: 0,
            right: 0,
            child: IgnorePointer(
              child: Center(
                child: Material(
                  elevation: 2,
                  shadowColor: Colors.black26,
                  shape: const CircleBorder(),
                  color: Theme.of(context).colorScheme.surface,
                  child: Padding(
                    padding: const EdgeInsets.all(10),
                    child: _status == RefreshIndicatorStatus.refresh
                        ? RotationTransition(
                            turns: _spinController,
                            child: Icon(Icons.refresh, size: 26, color: color),
                          )
                        : Transform.rotate(
                            angle: _pullRotation,
                            child: Icon(Icons.refresh, size: 26, color: color),
                          ),
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}

/// Scroll physics that allow pull-to-refresh even when content is short.
const alwaysScrollable = AlwaysScrollableScrollPhysics(
  parent: ClampingScrollPhysics(),
);
