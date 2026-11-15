package nl.buddyplan.display.ui

import nl.buddyplan.display.MaterialIconHelper
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ColorPaletteTest {

    @Test
    fun labelsMatchTheBrandbook() {
        // backend/app/services/color_palette.py BRAND_LABELS and mobile ColorPalette.labels
        assertEquals(
            listOf("rood", "oranje", "geel", "groen", "blauw", "teal", "paars", "bruin"),
            ColorPalette.LABELS,
        )
    }

    @Test
    fun hexToLabel() {
        assertEquals("groen", ColorPalette.hexToLabel(" Groen "))
        assertEquals("blauw", ColorPalette.hexToLabel("#3498DB")) // legacy palette
        assertEquals("rood", ColorPalette.hexToLabel("#FED7D7")) // exact brand background
        assertEquals("rood", ColorPalette.hexToLabel("#FFD0D0")) // nearest brand color
        assertNull(ColorPalette.hexToLabel("not-a-color"))
        assertNull(ColorPalette.hexToLabel(null))
    }

    @Test
    fun resolveLabelPrefersTheExplicitLabel() {
        assertEquals("paars", ColorPalette.resolveLabel(color = "#e74c3c", colorLabel = "Paars"))
        assertEquals("rood", ColorPalette.resolveLabel(color = "#e74c3c", colorLabel = "magenta"))
        assertNull(ColorPalette.resolveLabel(color = null))
    }

    @Test
    fun migrateStoredColorAlwaysReturnsALabel() {
        assertEquals("rood", ColorPalette.migrateStoredColor(""))
        assertEquals("rood", ColorPalette.migrateStoredColor("onzin"))
        assertEquals("teal", ColorPalette.migrateStoredColor("#1abc9c"))
    }

    @Test
    fun legacyIconIdsAreMappedToMaterialIcons() {
        assertEquals("md:dentistry", MaterialIconHelper.normalize("toothbrush"))
        assertEquals("custom:kliko-restafval", MaterialIconHelper.normalize("fas:trash"))
        assertEquals("md:home", MaterialIconHelper.normalize(" md:home "))
        assertEquals(MaterialIconHelper.DEFAULT_ICON, MaterialIconHelper.normalize("onbekend"))
        assertEquals(MaterialIconHelper.DEFAULT_ICON, MaterialIconHelper.normalize(null))
    }
}
