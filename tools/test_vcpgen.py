# Structural tests for tools/vcpgen.py (stdlib unittest; no pytest on dev box).
import os
import sys
import tempfile
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

    def test_lit_style_has_halo_but_no_filter(self):
        svg = vcpgen.render_button_svg(['X1'], 'lit')
        off = vcpgen.render_button_svg(['X1'], 'amber')
        # glow = two extra halo rects, never SVG filters
        self.assertEqual(svg.count('<rect'), off.count('<rect') + 2)
        for s in (svg, off):
            self.assertNotIn('<filter', s)
            self.assertNotIn('feGaussianBlur', s)

    def test_svg_safe_subset(self):
        # Svg2Xaml on the control PC only proves out absolute userSpaceOnUse
        # gradient coordinates and no filter primitives (see spec).
        import re as _re
        for style in vcpgen.STYLES:
            for svg in (vcpgen.render_button_svg(['A'], style),
                        vcpgen.render_reset_svg(False),
                        vcpgen.render_reset_svg(True),
                        vcpgen.render_nameplate_svg()):
                self.assertNotIn('<filter', svg)
                self.assertNotIn('feMerge', svg)
                # transform function lists stack glyphs at the origin on the
                # machine; only single matrix() transforms are proven safe
                self.assertNotIn('translate(', svg)
                self.assertNotIn('scale(', svg)
                for g in _re.findall(r'<(?:linear|radial)Gradient[^>]*>', svg):
                    self.assertIn('userSpaceOnUse', g)
                    self.assertNotIn('%', g)

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


class TestFeedrateKnob(unittest.TestCase):
    QUADS = ('NW', 'NE', 'SW', 'SE')

    def test_all_quadrants_render_and_parse(self):
        for q in self.QUADS:
            for on in (False, True):
                svg = vcpgen.render_feedrate_knob_svg(q, on)
                ET.fromstring(svg)
                svg.encode('ascii')

    def test_on_state_adds_a_needle(self):
        for q in self.QUADS:
            off = vcpgen.render_feedrate_knob_svg(q, False)
            on = vcpgen.render_feedrate_knob_svg(q, True)
            self.assertNotIn('fk-needle', off)
            self.assertIn('fk-needle', on)

    def test_needle_stays_inside_its_own_cell(self):
        # The whole design rests on this: each preset's needle must fall in
        # its own button's cell, because a VCP button can only swap its own
        # image. A needle crossing into a neighbour would be invisible.
        for q in self.QUADS:
            cx, cy, _, preset = vcpgen.FKNOB_QUADRANTS[q]
            th = vcpgen.FKNOB_THETA0 + vcpgen.FKNOB_SWEEP * preset / 100.0
            x, y = vcpgen._fk_pt(cx, cy, vcpgen.FKNOB_R_NEEDLE, th)
            self.assertTrue(0 <= x <= vcpgen.VB_W,
                            '%s needle x=%.1f outside cell' % (q, x))
            self.assertTrue(0 <= y <= vcpgen.VB_H,
                            '%s needle y=%.1f outside cell' % (q, y))

    def test_each_preset_owned_by_exactly_one_quadrant(self):
        presets = sorted(v[3] for v in vcpgen.FKNOB_QUADRANTS.values())
        self.assertEqual(presets, [25, 50, 75, 100])


class TestEmitButtons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = tempfile.mkdtemp(prefix='vcpgen_')
        vcpgen.emit_buttons(cls.out)
        cls.bdir = os.path.join(cls.out, 'resources', 'vcp', 'Buttons')

    def _read(self, *parts):
        with open(os.path.join(self.bdir, *parts)) as f:
            return f.read()

    def test_every_table_entry_has_folder_xml_svg(self):
        for b in vcpgen.BUTTONS:
            rn = 'retro_' + b['name']
            xml = self._read(rn, rn + '.xml')
            ET.fromstring(xml)
            self.assertTrue(os.path.exists(
                os.path.join(self.bdir, rn, rn + '.svg')))

    def test_stateful_led_becomes_image_swap(self):
        xml = self._read('retro_spindle_cw', 'retro_spindle_cw.xml')
        self.assertIn('<number>1063</number>', xml)       # PLC bit preserved
        self.assertIn('<image_on>retro_spindle_cw_on.svg</image_on>', xml)
        self.assertIn('<image_off>retro_spindle_cw.svg</image_off>', xml)
        self.assertNotIn('color_on', xml)
        self.assertTrue(os.path.exists(os.path.join(
            self.bdir, 'retro_spindle_cw', 'retro_spindle_cw_on.svg')))

    def test_momentary_has_single_svg(self):
        xml = self._read('retro_x_positive', 'retro_x_positive.xml')
        self.assertIn('<skin_event_num>39</skin_event_num>', xml)
        self.assertFalse(os.path.exists(os.path.join(
            self.bdir, 'retro_x_positive', 'retro_x_positive_on.svg')))

    def test_led_override_targets_plc_output_number(self):
        # PUMP watches the real pump output (OUT4), not the stock mist LED
        xml = self._read('retro_coolant_pump', 'retro_coolant_pump.xml')
        self.assertIn('<plc_output>\n\t\t<number>4</number>', xml)
        # unrelated buttons keep their stock PLC numbers unchanged
        cw = self._read('retro_spindle_cw', 'retro_spindle_cw.xml')
        self.assertIn('<number>1063</number>', cw)

    def test_reset_uses_retro_filenames(self):
        xml = self._read('retro_reset', 'retro_reset.xml')
        self.assertIn('<image_on>retro_reset_tripped.svg</image_on>', xml)
        self.assertIn('<image_off>retro_reset.svg</image_off>', xml)
        for f in ('retro_reset.svg', 'retro_reset_tripped.svg'):
            self.assertTrue(os.path.exists(
                os.path.join(self.bdir, 'retro_reset', f)))

    def test_legend_swap_pairs(self):
        # knob SVGs contain BOTH labels in both states; the active position
        # is amber (#e3ac5c), the inactive dim (#6a645c) - assert per state
        def label_fill(svg, label):
            import re as _re
            m = _re.search(r'fill="(#[0-9a-f]{6})"[^>]*>%s<' % label, svg)
            self.assertIsNotNone(m, 'label %s not found' % label)
            return m.group(1)

        on = self._read('retro_incr_cont', 'retro_incr_cont_on.svg')
        off = self._read('retro_incr_cont', 'retro_incr_cont.svg')
        # jog bit ON = INCR (verified on-machine); labels: (CONT, INCR)
        self.assertEqual(label_fill(on, 'INCR'), '#e3ac5c')
        self.assertEqual(label_fill(on, 'CONT'), '#6a645c')
        self.assertEqual(label_fill(off, 'CONT'), '#e3ac5c')
        self.assertEqual(label_fill(off, 'INCR'), '#6a645c')

    def test_all_emitted_files_ascii_and_crlf(self):
        for root, _dirs, files in os.walk(self.bdir):
            for f in files:
                with open(os.path.join(root, f), 'rb') as fh:
                    data = fh.read()
                self.assertTrue(max(data) < 128,
                                'non-ASCII byte in %s' % f)
                # CNC12 runs on Windows: every newline must be CRLF
                self.assertEqual(data.count(b'\n'), data.count(b'\r\n'),
                                 'bare LF in %s' % f)


class TestSkin(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = tempfile.mkdtemp(prefix='vcpgen_full_')
        vcpgen.generate(cls.out)

    def test_skin_parses_and_references_existing_buttons(self):
        skin_path = os.path.join(self.out, 'resources', 'vcp', 'skins',
                                 'acroloc_retro_vcp_skin.vcp')
        with open(skin_path) as f:
            skin = f.read()
        skin.encode('ascii')
        root = ET.fromstring(skin)
        names = [el.text for el in root.iter('button')]
        self.assertEqual(len(names), len(vcpgen.BUTTONS))
        for n in names:
            self.assertTrue(os.path.exists(os.path.join(
                self.out, 'resources', 'vcp', 'Buttons', n, n + '.xml')),
                'skin references missing button ' + str(n))

    def test_grid_positions_in_range(self):
        for b in vcpgen.BUTTONS:
            self.assertTrue(1 <= b['row'] <= 14 and 1 <= b['col'] <= 6)
            self.assertTrue(b['row'] + b.get('row_span', 1) - 1 <= 14)
            self.assertTrue(b['col'] + b.get('col_span', 1) - 1 <= 6)

    def test_no_duplicate_cells(self):
        seen = set()
        for b in vcpgen.BUTTONS:
            for r in range(b['row'], b['row'] + b.get('row_span', 1)):
                for c in range(b['col'], b['col'] + b.get('col_span', 1)):
                    self.assertNotIn((r, c), seen,
                                     'cell collision at %s' % ((r, c),))
                    seen.add((r, c))

    def test_nameplate_emitted(self):
        self.assertTrue(os.path.exists(os.path.join(
            self.out, 'resources', 'vcp', 'images',
            'acroloc_nameplate.svg')))

    def test_deterministic(self):
        out2 = tempfile.mkdtemp(prefix='vcpgen_det_')
        vcpgen.generate(out2)
        for root_dir, _dirs, files in os.walk(self.out):
            rel = os.path.relpath(root_dir, self.out)
            for f in files:
                a = os.path.join(root_dir, f)
                b = os.path.join(out2, rel, f)
                with open(a, 'rb') as fa, open(b, 'rb') as fb:
                    self.assertEqual(fa.read(), fb.read(),
                                     'nondeterministic: %s' % f)


if __name__ == '__main__':
    unittest.main()
