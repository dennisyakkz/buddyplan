import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'buddyplan_colors.dart';

class BuddyplanTheme {
  BuddyplanTheme._();

  static ThemeData light() {
    final heading = GoogleFonts.plusJakartaSansTextTheme();
    final body = GoogleFonts.interTextTheme();

    final colorScheme = ColorScheme.light(
      primary: BuddyplanColors.teal,
      onPrimary: Colors.white,
      secondary: BuddyplanColors.coral,
      surface: BuddyplanColors.card,
      onSurface: BuddyplanColors.slateDark,
      onSurfaceVariant: BuddyplanColors.mutedSlate,
      outline: BuddyplanColors.mutedGray,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: BuddyplanColors.background,
    );

    final inputBorder = OutlineInputBorder(
      borderRadius: BorderRadius.circular(BuddyplanColors.borderRadius),
      borderSide: const BorderSide(color: BuddyplanColors.mutedGray),
    );

    return base.copyWith(
      textTheme: body.copyWith(
        headlineSmall: heading.headlineSmall?.copyWith(
          color: BuddyplanColors.slateDark,
          fontWeight: FontWeight.w700,
        ),
        titleLarge: heading.titleLarge?.copyWith(
          color: BuddyplanColors.slateDark,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: heading.titleMedium?.copyWith(
          color: BuddyplanColors.slateDark,
          fontWeight: FontWeight.w600,
        ),
        titleSmall: heading.titleSmall?.copyWith(
          color: BuddyplanColors.slateDark,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: body.bodyLarge?.copyWith(color: BuddyplanColors.slateDark),
        bodyMedium: body.bodyMedium?.copyWith(color: BuddyplanColors.slateDark),
        bodySmall:
            body.bodySmall?.copyWith(color: BuddyplanColors.mutedSlate),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: BuddyplanColors.teal,
        foregroundColor: Colors.white,
        elevation: 0,
        titleTextStyle: GoogleFonts.plusJakartaSans(
          fontSize: 20,
          fontWeight: FontWeight.w700,
          color: Colors.white,
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: BuddyplanColors.card,
        indicatorColor: BuddyplanColors.teal.withValues(alpha: 0.12),
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.inter(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: BuddyplanColors.teal,
            );
          }
          return GoogleFonts.inter(
            fontSize: 12,
            color: BuddyplanColors.mutedSlate,
          );
        }),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) return Colors.white;
          return Colors.white;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return BuddyplanColors.teal;
          }
          return BuddyplanColors.mutedGray;
        }),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: BuddyplanColors.card,
        border: inputBorder,
        enabledBorder: inputBorder,
        focusedBorder: inputBorder.copyWith(
          borderSide: const BorderSide(color: BuddyplanColors.teal, width: 2),
        ),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: BuddyplanColors.teal,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius:
                BorderRadius.circular(BuddyplanColors.borderRadius),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: GoogleFonts.plusJakartaSans(
            fontWeight: FontWeight.w600,
            fontSize: 16,
          ),
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: BuddyplanColors.teal,
        foregroundColor: Colors.white,
        elevation: 1,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(BuddyplanColors.borderRadius),
        ),
      ),
      cardTheme: CardThemeData(
        color: BuddyplanColors.card,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius:
              BorderRadius.circular(BuddyplanColors.borderRadius),
          side: const BorderSide(color: BuddyplanColors.mutedGray),
        ),
      ),
    );
  }

  static ThemeData dark() {
    final heading = GoogleFonts.plusJakartaSansTextTheme(ThemeData.dark().textTheme);
    final body = GoogleFonts.interTextTheme(ThemeData.dark().textTheme);

    final colorScheme = ColorScheme.dark(
      primary: BuddyplanColors.teal,
      onPrimary: Colors.white,
      secondary: BuddyplanColors.coral,
      surface: const Color(0xFF2D3748),
      onSurface: BuddyplanColors.paleGray,
      onSurfaceVariant: const Color(0xFFA0AEC0),
      outline: BuddyplanColors.borderDark,
    );

    final base = ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: BuddyplanColors.deepCharcoal,
      brightness: Brightness.dark,
    );

    final inputBorder = OutlineInputBorder(
      borderRadius: BorderRadius.circular(BuddyplanColors.borderRadius),
      borderSide: const BorderSide(color: BuddyplanColors.borderDark),
    );

    return base.copyWith(
      textTheme: body.copyWith(
        titleLarge: heading.titleLarge?.copyWith(
          color: BuddyplanColors.paleGray,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: heading.titleMedium?.copyWith(
          color: BuddyplanColors.paleGray,
          fontWeight: FontWeight.w600,
        ),
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: BuddyplanColors.darkTeal,
        foregroundColor: Colors.white,
        elevation: 0,
        titleTextStyle: GoogleFonts.plusJakartaSans(
          fontSize: 20,
          fontWeight: FontWeight.w700,
          color: Colors.white,
        ),
      ),
      switchTheme: SwitchThemeData(
        trackColor: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return BuddyplanColors.teal;
          }
          return BuddyplanColors.borderDark;
        }),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFF2D3748),
        border: inputBorder,
        enabledBorder: inputBorder,
        focusedBorder: inputBorder.copyWith(
          borderSide: const BorderSide(color: BuddyplanColors.teal, width: 2),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: BuddyplanColors.teal,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius:
                BorderRadius.circular(BuddyplanColors.borderRadius),
          ),
        ),
      ),
      floatingActionButtonTheme: const FloatingActionButtonThemeData(
        backgroundColor: BuddyplanColors.teal,
        foregroundColor: Colors.white,
        elevation: 1,
      ),
    );
  }
}
