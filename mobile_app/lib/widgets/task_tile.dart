import 'package:flutter/material.dart';
import '../models/task_item.dart';
import '../ui/task_color_utils.dart';

class TaskTile extends StatelessWidget {
  final TaskItem task;
  final Color? personColor;
  final VoidCallback? onComplete;
  final VoidCallback? onOpen;
  final bool canComplete;
  final bool dense;

  const TaskTile({
    super.key,
    required this.task,
    this.personColor,
    this.onComplete,
    this.onOpen,
    this.canComplete = true,
    this.dense = false,
  });

  @override
  Widget build(BuildContext context) {
    final completed = task.completed;
    final baseColor = personColor ?? Theme.of(context).colorScheme.primary;
    final bgColor = completed
        ? Theme.of(context).colorScheme.surfaceContainerHighest
        : adaptTaskColorForTheme(baseColor, context);
    final textColor = completed
        ? Theme.of(context).colorScheme.onSurfaceVariant
        : contrastColorForBackground(bgColor);

    return Padding(
      padding: EdgeInsets.symmetric(
        horizontal: dense ? 8 : 12,
        vertical: dense ? 2 : 4,
      ),
      child: Material(
        color: bgColor,
        borderRadius: BorderRadius.circular(8),
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
              decoration: completed ? TextDecoration.lineThrough : null,
            ),
          ),
          subtitle: task.description.isNotEmpty
              ? Text(
                  task.description,
                  style: TextStyle(
                    color: textColor.withValues(alpha: 0.85),
                  ),
                )
              : null,
          trailing: completed
              ? Icon(Icons.check_circle, color: textColor.withValues(alpha: 0.8))
              : (canComplete && onComplete != null)
                  ? IconButton(
                      icon: Icon(Icons.radio_button_unchecked, color: textColor),
                      onPressed: onComplete,
                      tooltip: 'Markeer als gedaan',
                    )
                  : null,
        ),
      ),
    );
  }
}
