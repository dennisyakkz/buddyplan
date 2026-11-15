import 'package:buddyplan_mobile/ui/color_palette.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('normalizeLabel falls back to teal', () {
    expect(ColorPalette.normalizeLabel('Rood'), 'rood');
    expect(ColorPalette.normalizeLabel(' paars '), 'paars');
    expect(ColorPalette.normalizeLabel(null), 'teal');
    expect(ColorPalette.normalizeLabel('magenta'), 'teal');
  });

  test('labels match the backend brandbook labels', () {
    // backend/app/services/color_palette.py BRAND_LABELS
    expect(ColorPalette.labels,
        ['rood', 'oranje', 'geel', 'groen', 'blauw', 'teal', 'paars', 'bruin']);
  });

  Future<BuildContext> contextWith(
      WidgetTester tester, Brightness brightness) async {
    late BuildContext captured;
    await tester.pumpWidget(
      MaterialApp(
        theme: ThemeData(brightness: brightness),
        home: Builder(builder: (context) {
          captured = context;
          return const SizedBox();
        }),
      ),
    );
    await tester.pumpAndSettle(); // MaterialApp animates theme changes
    return captured;
  }

  testWidgets('chip colors switch between light and dark mode', (tester) async {
    final light = ColorPalette.chipStyle(
        await contextWith(tester, Brightness.light), 'rood');
    expect(light.background, const Color(0xFFFED7D7));
    expect(light.text, const Color(0xFF9B2C2C));

    final dark = ColorPalette.chipStyle(
        await contextWith(tester, Brightness.dark), 'rood');
    expect(dark.background, const Color(0xFF9B2C2C));
    expect(dark.text, const Color(0xFFFFF5F5));
  });

  testWidgets('dots always use the saturated color', (tester) async {
    final context = await contextWith(tester, Brightness.dark);
    expect(ColorPalette.dotColor(context, 'groen'), const Color(0xFF22543D));
  });
}
