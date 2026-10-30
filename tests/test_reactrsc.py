"""Regression tests for resources.lib.reactrsc.RSCHelper.

Run from the project root with:
    python -m unittest -v test_reactrsc

The tests use miniature Flight streams rather than any website-specific data.
"""

import unittest


def text_record(record_id: str, text: str) -> str:
    """Produce a valid Flight T record with a hexadecimal UTF-8 byte length."""
    return f"{record_id}:T{len(text.encode('utf-8')):x},{text}"


class RSCHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """ Setup the required elements for channels to run """

        from resources.lib.logger import Logger
        Logger.create_logger(None, str(cls), min_log_level=0)

    @classmethod
    def tearDownClass(cls):
        from resources.lib.addonsettings import AddonSettings
        AddonSettings.clear_cached_addon_settings_object()

    def convert(self, content: str):
        from resources.lib.helpers.reactrsc import RSCHelper
        return RSCHelper(content).convert_to_json()

    def test_plain_json_root(self):
        self.assertEqual(
            self.convert('0:{"name":"example","count":3,"active":true,"empty":null}\n'),
            {"name": "example", "count": 3, "active": True, "empty": None},
        )

    def test_reference_types_and_forward_references(self):
        content = '\n'.join([
            '0:{"direct":"$1","lazy":"$L2","nested":["$L3"]}',
            '3:{"value":"yes"}',
            '2:[1,2,3]',
            '1:"hello"',
        ])
        self.assertEqual(self.convert(content), {
            'direct': 'hello', 'lazy': [1, 2, 3], 'nested': [{'value': 'yes'}]
        })

    def test_q_map_reaches_descendant_records(self):
        content = '\n'.join([
            '0:{"route":"$Q6"}',
            '6:[["children",{"children":"$L20"}]]',
            '20:["$","div",null,{"children":"$L22"}]',
            '22:{"dehydratedState":{"queries":[{"data":"found"}]}}',
        ])
        # pyrefly: ignore [bad-index]
        route = self.convert(content)['route']['__map__']
        self.assertEqual(
            route[0][1]['children'][3]['children']['dehydratedState']['queries'][0]['data'],
            'found',
        )

    def test_promise_reference(self):
        result = self.convert('0:{"result":"$@c"}\nc:{"ready":true}\n')
        self.assertEqual(result, {'result': {'__promise__': {'ready': True}}})

    def test_undefined_symbol_and_react_element_marker(self):
        result = self.convert('0:["$","div",null,{"unused":"$undefined","symbol":"$Sreact.fragment"}]\n')
        self.assertEqual(result, ['$', 'div', None, {
            'unused': None, 'symbol': {'__symbol__': 'react.fragment'}
        }])

    def test_module_import_record(self):
        result = self.convert('0:{"component":"$3"}\n3:I[339756,["chunk.js"],"default"]\n')
        self.assertEqual(result, {
            'component': {'__module__': [339756, ['chunk.js'], 'default']}
        })

    def test_multiline_text_record_preserves_newlines(self):
        body = 'first line\nsecond line\nthird line'
        stream = '0:{"content":"$4b"}\n' + text_record('4b', body) + '\n'
        # pyrefly: ignore [bad-index]
        self.assertEqual(self.convert(stream)['content'], body)

    def test_t_record_uses_utf8_bytes_not_character_count(self):
        body = 'één café 😀'
        stream = '0:{"content":"$4b"}\n' + text_record('4b', body) + '\n'
        # pyrefly: ignore [bad-index]
        self.assertEqual(self.convert(stream)['content'], body)

    def test_concatenated_t_records_preserve_m3u8_url(self):
        # The regression: record 4c begins immediately after the text in 4b.
        url = 'https://cdn.example.org/show/cmaf/master.m3u8?policy=abc123'
        body = 'Beschrijving met é en regels\nregel twee\n'
        stream = (
            '0:{"stream":{"url":"$4c"},"description":"$4b"}\n'
            + text_record('4b', body)
            + text_record('4c', url)
            + '\n'
        )
        result = self.convert(stream)
        # pyrefly: ignore [bad-index]
        self.assertEqual(result['description'], body)
        # pyrefly: ignore [bad-index]
        self.assertEqual(result['stream']['url'], url)

    def test_t_record_can_be_followed_by_json_record_without_newline(self):
        stream = (
            '0:{"text":"$4a","next":"$48"}\n'
            + text_record('4a', 'café')
            + '48:{"ok":true}\n'
        )
        self.assertEqual(self.convert(stream), {'text': 'café', 'next': {'ok': True}})

    def test_lf_and_crlf_record_separators(self):
        stream = '0:{"data":"$1"}\r\n1:"ok"\r\n'
        self.assertEqual(self.convert(stream), {'data': 'ok'})

    def test_circular_references_do_not_recurse_forever(self):
        stream = '0:{"next":"$1"}\n1:{"previous":"$0"}\n'
        self.assertEqual(self.convert(stream), {'next': {'previous': {'next': '[Circular]'}}})

    def test_missing_root_raises(self):
        with self.assertRaisesRegex(ValueError, 'No root record'):
            self.convert('1:{"orphan":true}\n')

    def test_incomplete_text_record_raises(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete Flight text record'):
            self.convert('0:{"text":"$4b"}\n4b:Tff,short')

    def test_malformed_json_records_are_ignored(self):
        self.assertEqual(self.convert('bad:not-json\n0:{"ok":true}\n'), {'ok': True})

    def test_repeated_references_in_sibling_branches_are_not_circular(self):
        self.assertEqual(
            self.convert('0:{"a":"$1","b":"$1"}\n1:{"name":"same"}\n'),
            {'a': {'name': 'same'}, 'b': {'name': 'same'}},
        )


if __name__ == '__main__':
    unittest.main()
