import 'package:flutter/material.dart';
import 'package:flutter_svg/flutter_svg.dart';
import 'buddyplan_logo_paths.dart';

enum BuddyplanLogoVariant {
  /// Brand teal/coral on light backgrounds (login, auth).
  color,
  /// White paths on teal/dark headers (brandbook §7.1).
  inverse,
}

class BuddyplanLogo extends StatelessWidget {
  final double size;
  final BuddyplanLogoVariant variant;

  const BuddyplanLogo({
    super.key,
    this.size = 120,
    this.variant = BuddyplanLogoVariant.color,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: SvgPicture.string(
        _svgForVariant(variant),
        fit: BoxFit.contain,
      ),
    );
  }

  String _svgForVariant(BuddyplanLogoVariant variant) {
    if (variant == BuddyplanLogoVariant.inverse) {
      return _buildSvg(
        bodyFill: '#FFFFFF',
        squareFill: '#FFFFFF',
        squareOpacity: 0.3,
      );
    }
    return _buildSvg(
      tealFill: '#2C6A6B',
      coralFill: '#D8745E',
      tealSquareFill: '#2C6A6B',
      coralSquareFill: '#D8745E',
      squareOpacity: 0.4,
    );
  }

  String _buildSvg({
    String? tealFill,
    String? coralFill,
    String? bodyFill,
    String? tealSquareFill,
    String? coralSquareFill,
    String? squareFill,
    required double squareOpacity,
  }) {
    final tealBodyColor = bodyFill ?? tealFill!;
    final coralBodyColor = bodyFill ?? coralFill!;
    final tealSquareColor = squareFill ?? tealSquareFill!;
    final coralSquareColor = squareFill ?? coralSquareFill!;

    String path(String d, String fill, {double? opacity}) {
      final opacityAttr =
          opacity != null ? ' fill-opacity="$opacity"' : '';
      return '<path fill="$fill"$opacityAttr d="$d"/>';
    }

    final parts = <String>[
      for (final d in BuddyplanLogoPaths.tealBodies)
        path(d, tealBodyColor),
      for (final d in BuddyplanLogoPaths.coralBodies)
        path(d, coralBodyColor),
      path(BuddyplanLogoPaths.tealSquare, tealSquareColor,
          opacity: squareOpacity),
      path(BuddyplanLogoPaths.coralSquare, coralSquareColor,
          opacity: squareOpacity),
    ];

    return '<svg xmlns="http://www.w3.org/2000/svg" '
        'viewBox="${BuddyplanLogoPaths.viewBox}">${parts.join()}</svg>';
  }
}
