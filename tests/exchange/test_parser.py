"""Literal malformed/Unicode/numeric/budget parser tests, independent expectations."""
import json
import hashlib
import time
from support import ALGORITHM, ExchangeCLI


class ParserConformance(ExchangeCLI):
    def test_all_independent_literal_canonical_vectors(self):
        for i in range(39):
            name = "C%02d.json" % i
            with self.subTest(name=name):
                data = (ALGORITHM / name).read_bytes()
                self.accepts("parse", data, data)

    def test_utf8_object_order_not_utf16_or_signed_bytes(self):
        self.accepts("parse", '{"𐀀":"supp","a":"ascii","\ue000":"bmp"}'.encode(),
                     (ALGORITHM / "C02.json").read_bytes())
        self.accepts("parse", b'{"\\ud800\\udc00":"supp","a":"ascii","\\ue000":"bmp"}',
                     (ALGORITHM / "C02.json").read_bytes())

    def test_escaping_and_unicode_are_not_normalized(self):
        self.accepts("parse", b'{"text":"\\u0022\\u005c\\/\\u0008\\u000C\\u000a\\u000d\\u0009\\u0000\\u0001\\u000B\\u001F"}',
                     (ALGORITHM / "C03.json").read_bytes())
        self.accepts("parse", b'{"x":"\\ud800\\udc00"}', '{"x":"𐀀"}'.encode())
        self.accepts("parse", '{"é":0,"é":1}'.encode(), '{"é":1,"é":0}'.encode())
        self.accepts("parse", '{"x":"\ufeff"}'.encode(), '{"x":"\ufeff"}'.encode())

    def test_duplicate_decoded_keys_at_every_object_level(self):
        cases = [
            (b'{"a":0,"a":1}', ["a"]),
            (b'{"a":0,"\\u0061":1}', ["a"]),
            (b'{"x":{"a":0,"\\u0061":1}}', ["x", "a"]),
            (b'{"annotations":{"golden.example/review":{"x":0,"\\u0078":1}}}', ["annotations", "golden.example/review", "x"]),
            (b'{"/":0,"\\/":1}', ["/"]),
            (b'{"~":0,"\\u007e":1}', ["~"]),
            (bytes.fromhex("7b22c3a9223a302c225c7530306539223a317d"), ["é"]),
            (b'{"\\ud800\\udc00":0,"\\uD800\\uDC00":1}', ["𐀀"]),
            (b'{"body":{},"body":{}}', ["body"]),
        ]
        for data, path in cases:
            with self.subTest(data=data):
                self.rejects("parse", data, "duplicate_key", path=path)

    def test_long_duplicate_key_has_exact_pointer_and_bounded_presentation(self):
        key="é"*1000+"a`b/~"
        token=json.dumps(key,ensure_ascii=False).encode()
        data=b'{"nested":{'+token+b':0,'+token+b':1}}'
        error=self.rejects("parse",data,"duplicate_key",path=["nested",key])
        for field in ["message","actual","expected"]:
            if error.get(field) is not None:
                self.assertLessEqual(len(error[field].encode("utf-8")),1024)
        self.assertNotIn(key,error["message"])

    def test_deep_large_key_pointer_remains_exact_without_message_amplification(self):
        # 64 object containers and 65 admitted key tokens: 4.26 MiB input,
        # below 8 MiB. The final key duplicates at depth 64. This stresses pointer
        # composition without exceeding a string/container budget first.
        key="a"*(65536-2)+"/~"
        token=json.dumps(key).encode()
        raw=b"{"+token+b":0,"+token+b":0}"
        for _ in range(63):raw=b"{"+token+b":"+raw+b"}"
        expected=("/"+key.replace("~","~0").replace("/","~1"))*64
        self.assertLess(len(raw),8388608)
        self.assertGreater(len(expected),4_000_000)
        started=time.monotonic()
        result=self.invoke("parse",raw)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(result.stdout,b"")
        error=json.loads(result.stderr)
        self.assertEqual(error["code"],"duplicate_key")
        self.assertEqual(error["stage"],"parse")
        self.assertEqual(error["pointer"],expected)
        self.assertTrue(error["remedy"])
        for field in ["message","actual","expected"]:
            if error.get(field) is not None:
                self.assertLessEqual(len(error[field].encode("utf-8")),1024)
        self.assertNotIn(key,error["message"])
        print("EXCHANGE_DIAGNOSTIC "+json.dumps({"input_bytes":len(raw),"depth":64,
            "input_sha256":hashlib.sha256(raw).hexdigest(),"pointer_bytes":len(expected.encode()),
            "message_bytes":len(error["message"].encode()),
            "elapsed_seconds":round(time.monotonic()-started,6)},sort_keys=True))

    def test_malformed_utf8_rejects_without_replacement(self):
        for raw in ["7b2278223a22c080227d", "7b2278223a22eda080227d", "7b2278223a22f4908080227d",
                    "7b2278223a22f09f98227d", "7b2278223a2280227d"]:
            with self.subTest(hex=raw):
                self.rejects("parse", bytes.fromhex(raw), "invalid_utf8")

    def test_json_surrogate_escape_truncation_and_bom_failures(self):
        cases = [b'{"x":"\\ud800"}', b'{"x":"\\udc00"}', b'{"x":"\\ud800A"}',
                 b'{"x":"\\udc00\\ud800"}', b'{"x":"\\q"}', b'{"x":"\\u00G0"}',
                 bytes.fromhex("7b2278223a2200227d"), b'\xef\xbb\xbf{}', b'{"x":',
                 b'{"x":"a}', b'[', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}',
                 b'{"x":01}', b'{"x":+1}', b'{"x":}', b'{"x":0,}']
        for data in cases:
            with self.subTest(data=data):
                self.rejects("parse", data, "invalid_json")

    def test_trailing_document_is_distinct_from_whitespace(self):
        self.accepts("parse", b' \n{}\r\t ', b'{}')
        for data in [b'{}{}', b'{} 0', b'[] null']:
            with self.subTest(data=data):
                self.rejects("parse", data, "trailing_document")

    def test_integer_lexemes_forbid_negative_zero_fractions_and_exponents(self):
        for spelling in [b'-0', b'1.0', b'1e0', b'-0.0', b'-0e0', b'1E+0']:
            with self.subTest(spelling=spelling):
                self.rejects("parse", b'{"x":' + spelling + b'}', "invalid_json")
        self.accepts("parse", b'{"x":0,"y":-2147483648,"z":2147483647}',
                     b'{"x":0,"y":-2147483648,"z":2147483647}')

    def test_unrepresentable_numeric_literals_never_become_semantic_u64(self):
        self.rejects("parse",b'{"x":18446744073709551615}',"overflow")
        for literal in [b'18446744073709551616',b'9'*400,b'1e999999']:
            self.rejects("parse",b'{"x":'+literal+b'}',"invalid_json")

    def test_exact_small_input_limits_count_raw_whitespace(self):
        data = b'{"a":0}'
        self.accepts("parse", data, data, limits={"input_bytes": 7})
        self.rejects("parse", data, "limit", limits={"input_bytes": 6})
        self.rejects("parse", data + b' ', "limit", limits={"input_bytes": 7})

    def test_exact_small_node_counts_include_keys(self):
        for data, count in [(b'{}', 1), (b'{"a":0}', 3), (b'{"a":[]}', 3),
                            (b'{"a":[0]}', 4), (b'{"a":0,"b":1}', 5), (b'{"a":[0,1]}', 5)]:
            with self.subTest(data=data):
                self.accepts("parse", data, data, limits={"nodes": count})
                if count > 1:
                    self.rejects("parse", data, "limit", limits={"nodes": count-1})

    def test_container_depth_not_scalar_or_key_depth(self):
        self.accepts("parse", b'{"a":0}', b'{"a":0}', limits={"nesting": 1})
        for data in [b'{"a":[]}', b'{"a":[0]}']:
            self.rejects("parse", data, "limit", path=["a"], limits={"nesting": 1})
            self.accepts("parse", data, data, limits={"nesting": 2})
        for depth in [64, 65]:
            values = [b'['*depth+b'0'+b']'*depth,
                      b'{"a":'*depth+b'0'+b'}'*depth]
            mixed = b'0'
            for n in range(depth):
                mixed = b'['+mixed+b']' if n%2 else b'{"a":'+mixed+b'}'
            values.append(mixed)
            for data in values:
                with self.subTest(depth=depth, prefix=data[:12]):
                    if depth == 64:
                        self.accepts("parse", data, data)
                    else:
                        self.rejects("parse", data, "limit")

    def test_immediate_entries_are_members_or_elements(self):
        for data, path in [(b'{"a":0,"b":1}', []), (b'{"a":[0,1]}', ["a", 1])]:
            self.accepts("parse", data, data, limits={"collection": 2})
            self.rejects("parse", data, "limit", path=path, limits={"collection": 1})

    def test_decoded_strings_and_keys_count_utf8_bytes(self):
        data = '{"a":"é"}'.encode()
        self.accepts("parse", data, data, limits={"string_bytes": 2})
        self.accepts("parse", b'{"a":"\\u00e9"}', data, limits={"string_bytes": 2})
        self.rejects("parse", data, "limit", path=["a"], limits={"string_bytes": 1})
        self.rejects("parse", '{"é":0}'.encode(), "limit", limits={"string_bytes": 1})

    def test_default_budget_boundaries(self):
        self.accepts("parse", b' '*(8388608-2)+b'{}', b'{}')
        self.rejects("parse", b' '*(8388608-1)+b'{}', "limit")
        collection=b'['+b'0,'*16383+b'0]'
        self.accepts("parse", collection, collection)
        self.rejects("parse", b'['+b'0,'*16384+b'0]', "limit")
        string=b'{"x":"'+b'a'*65536+b'"}'
        self.accepts("parse", string, string)
        self.rejects("parse", b'{"x":"'+b'a'*65537+b'"}', "limit")
        groups=[b'['+b'0,'*16382+b'0]']*12
        tail=b'['+b'0,'*3389+b'0]'
        nodes=b'['+b','.join(groups+[tail])+b']'
        self.accepts("parse", nodes, nodes)  # 1 + 13 + 12*16383 + 3390 = 200000
        self.rejects("parse", b'['+b','.join(groups+[b'['+b'0,'*3390+b'0]'])+b']', "limit")

    def test_limits_are_positive_and_cannot_raise_ceilings(self):
        ceilings={"input_bytes":8388608,"nesting":64,"nodes":200000,"collection":16384,
                  "string_bytes":65536,"artifacts":256,"artifact_bytes":33554432}
        for name, ceiling in ceilings.items():
            for value in [0, ceiling+1]:
                with self.subTest(name=name,value=value):
                    self.rejects("parse", b'{}', "invalid_limits", limits={name:value})
