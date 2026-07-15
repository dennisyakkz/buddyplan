import 'package:flutter/material.dart';
import '../models/task_item.dart';
import '../ui/buddyplan_colors.dart';
import '../ui/color_palette.dart';

class TaskTile extends StatelessWidget {
  final TaskItem task;
  final String? profileColor;
  final VoidCallback? onComplete;
  final VoidCallback? onOpen;
  final bool canComplete;
  final bool dense;

  const TaskTile({
    super.key,
    required this.task,
    this.profileColor,
    this.onComplete,
    this.onOpen,
    this.canComplete = true,
    this.dense = false,
  });

  @override
  Widget build(BuildContext context) {
    final completed = task.completed;
    final accent = ColorPalette.accentColor(context, profileColor);
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDark ? const Color(0xFF2D3748) : BuddyplanColors.card;
    final borderColor =
        isDark ? BuddyplanColors.borderDark : BuddyplanColors.mutedGray;
    final textColor = completed
        ? Theme.of(context).colorScheme.onSurfaceVariant
        : Theme.of(context).colorScheme.onSurface;

    final card = Container(
      decoration: BoxDecoration(
        color: cardBg,
        borderRadius: BorderRadius.circular(BuddyplanColors.borderRadius),
        border: Border.all(color: borderColor, width: 1),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            width: 3,
            decoration: BoxDecoration(
              color: accent,
              borderRadius: const BorderRadius.horizontal(
                left: Radius.circular(BuddyplanColors.borderRadius),
              ),
            ),
          ),
          Expanded(
            child: ListTile(
              dense: dense,
              onTap: onOpen,
              contentPadding: EdgeInsets.symmetric(
                horizontal: dense ? 12 : 16,
                vertical: dense ? 0 : 4,
              ),
              title: Text(
                task.title,
                style: TextStyle(
                  color: textColor,
                  fontWeight: FontWeight.w500,
                ),
              ),
              subtitle: task.description.isNotEmpty
                  ? Text(
                      task.description,
                      style: TextStyle(
                        color: textColor.withValues(alpha: 0.75),
                      ),
                    )
                  : null,
              trailing: completed
                  ? Icon(
                      Icons.check_circle,
                      color: accent.withValues(alpha: 0.7),
                    )
                  : (canComplete && onComplete != null)
                      ? IconButton(
                          icon: Icon(
                            Icons.radio_button_unchecked,
                            color: accent,
                          ),
                          onPressed: onComplete,
                          tooltip: 'Markeer als gedaan',
                        )
                      : null,
            ),
          ),
        ],
      ),
    );

    return Padding(
      padding: EdgeInsets.symmetric(
        horizontal: dense ? 8 : 12,
        vertical: dense ? 2 : 4,
      ),
      child: completed
          ? Opacity(opacity: 0.4, child: card)
          : card,
    );
  }
}
