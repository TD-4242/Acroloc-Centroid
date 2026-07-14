# Structural tests for tools/vcpgen.py (stdlib unittest; no pytest on dev box).
import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vcpgen


class TestButtonSvg(unittest.TestCase):
    def test_amber_button_parses_and_is_ascii(self):
        svg = vcpgen.render_button_svg(['SPIN', '100%'], 'amber')
        svg.encode('ascii')                      # raises if non-ASCII
        root = ET.fromstring(svg)                # raises if malformed
        self.assertEqual(root.get('width'), '100')
        self.assertEqual(root.get('height'), '84')
        self.assertEqual(root.get('viewBox'), '0 0 116 97')

    def test_no_text_anchor_and_explicit_x(self):
        svg = vcpgen.render_button_svg(['FLOOD'], 'amber')
        self.assertNotIn('text-anchor', svg)
        self.assertIn('<text x="', svg)

    def test_lit_style_has_glow(self):
        svg = vcpgen.render_button_svg(['X1'], 'lit')
        self.assertIn('feGaussianBlur', svg)
        off = vcpgen.render_button_svg(['X1'], 'amber')
        self.assertNotIn('feGaussianBlur', off)

    def test_span_widens_artboard(self):
        svg = vcpgen.render_button_svg(['RESET'], 'red', span=3)
        root = ET.fromstring(svg)
        self.assertEqual(root.get('width'), '300')
        self.assertEqual(root.get('viewBox'), '0 0 348 97')

    def test_text_width_monotonic(self):
        self.assertLess(vcpgen.text_width('I', 15), vcpgen.text_width('W', 15))
        self.assertAlmostEqual(vcpgen.text_width('', 15), 0.0)


class TestIcons(unittest.TestCase):
    def test_all_icons_render(self):
        for key in ('up', 'down', 'left', 'right', 'cw', 'ccw', 'wheel',
                    'pump', 'flood', 'hare', 'tortoise'):
            svg = vcpgen.render_button_svg([], 'amber', icon=vcpgen.ICONS[key])
            svg.encode('ascii')
            ET.fromstring(svg)
            self.assertNotIn('FILL', svg)
            self.assertNotIn('CX', svg)


class TestNameplate(unittest.TestCase):
    def test_nameplate_parses(self):
        svg = vcpgen.render_nameplate_svg()
        svg.encode('ascii')
        root = ET.fromstring(svg)
        self.assertEqual(root.get('viewBox'), '0 0 634 100')
        # ACROLOC = 7 glyph paths
        self.assertEqual(svg.count('fill-rule="evenodd"'), 7)


class TestReset(unittest.TestCase):
    def test_reset_states(self):
        normal = vcpgen.render_reset_svg(False)
        tripped = vcpgen.render_reset_svg(True)
        for svg in (normal, tripped):
            svg.encode('ascii')
            ET.fromstring(svg)
        self.assertIn('RESET', normal)
        self.assertNotIn('TRIPPED', normal)
        self.assertIn('TRIPPED', tripped)


if __name__ == '__main__':
    unittest.main()
