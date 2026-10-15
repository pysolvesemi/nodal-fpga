"""Bounded independent axes, not a production-scale or hard-memory claim."""
import copy
import hashlib
import json
import random
import time
from support import GOLDENS, ExchangeCLI, P0, encoded, fixture, resign_architecture


def chain(depth):
    doc=fixture("architecture-high-u64")
    leaf=copy.deepcopy(doc["body"]["templates"][0])
    templates=[]
    for i in range(depth):
        name="t%02d"%i
        if i==depth-1:
            template=copy.deepcopy(leaf);template["key"]["local"]=name
        else:
            target=copy.deepcopy(leaf["key"]);target["local"]="t%02d"%(i+1)
            key=copy.deepcopy(leaf["key"]);key["local"]=name
            template={"children":[{"name":"c%02d"%(i+1),"template":target,"partition":None,"domains":[],"provenance":copy.deepcopy(P0)}],
                      "connections":[],"features":[],"key":key,"mode_groups":[],"provenance":copy.deepcopy(P0),"resources":[],"storage":[]}
        templates.append(template)
    doc["body"]["templates"]=templates
    doc["body"]["roots"][0]["template"]["local"]="t00"
    return resign_architecture(doc)


class ScaleConformance(ExchangeCLI):
    def test_repetition_axis_retains_one_definition_and_stable_literal_meaning(self):
        for count in [1,16,256,4096]:
            doc=fixture("architecture-high-u64")
            root=doc["body"]["roots"][0]
            doc["body"]["roots"]=[dict(copy.deepcopy(root),name="r%04d"%i) for i in range(count)]
            doc=resign_architecture(doc);expected=encoded(doc)
            started=time.monotonic()
            for _ in range(2):
                actual=json.loads(self.accepts("arch",doc,expected))
                self.assertEqual(len(actual["body"]["templates"]),1)
                self.assertEqual(len(actual["body"]["roots"]),count)
                self.assertEqual(actual["body"]["templates"][0]["storage"][0]["bits"],"18446744073709551615")
            print("EXCHANGE_SCALE "+json.dumps({"axis":"roots","count":count,"input_bytes":len(expected),
                "input_sha256":hashlib.sha256(expected).hexdigest(),"semantic_id":doc["body"]["semantic_id"],
                "repeats":2,"elapsed_seconds":round(time.monotonic()-started,6)},sort_keys=True))

    def test_template_depth_axis_boundary_and_no_flattening(self):
        for depth in [1,2,16,64]:
            doc=chain(depth);expected=encoded(doc)
            started=time.monotonic()
            actual=json.loads(self.accepts("arch",doc,expected))
            self.assertEqual(len(actual["body"]["templates"]),depth)
            self.assertEqual(len(actual["body"]["roots"]),1)
            self.assertEqual(sum(len(t["resources"]) for t in actual["body"]["templates"]),1)
            print("EXCHANGE_SCALE "+json.dumps({"axis":"template_depth","depth":depth,"input_bytes":len(expected),
                "input_sha256":hashlib.sha256(expected).hexdigest(),"elapsed_seconds":round(time.monotonic()-started,6)},sort_keys=True))
        self.rejects("arch",chain(65),"semantic",core="limit")

    def test_seeded_keyed_permutations_keep_pins_and_mux_sources_exact(self):
        original=fixture();expected=encoded(original)
        for seed in [0,1,17,365,65535]:
            doc=copy.deepcopy(original);rng=random.Random(seed)
            rng.shuffle(doc["body"]["roots"]);rng.shuffle(doc["body"]["domains"])
            rng.shuffle(doc["body"]["connections"])
            rng.shuffle(doc["body"]["templates"][0]["resources"])
            self.accepts("arch",doc,expected)

    def test_cold_payload_length_axes_keep_semantics_and_record_size_time(self):
        projection=(GOLDENS/"architecture.projection.json").read_bytes()
        identity=fixture()["body"]["semantic_id"]
        seen_raw=set()
        for axis,lengths in [("annotation_bytes",[0,1,128,1024,16384,65536]),
                             ("provenance_bytes",[0,1,128,1024])]:
            for length in lengths:
                doc=fixture()
                text="é"*(length//2)+"x"*(length%2)
                self.assertEqual(len(text.encode("utf-8")),length)
                if axis=="annotation_bytes":
                    doc["annotations"]["golden.example/review"]={"payload":text}
                else:
                    doc["body"]["provenance"]["display"]=text
                expected=encoded(doc)
                raw=b" \n"+expected+b"\n"
                raw_digest=hashlib.sha256(raw).hexdigest()
                self.assertNotIn(raw_digest,seen_raw);seen_raw.add(raw_digest)
                started=time.monotonic()
                for _ in range(2):
                    self.accepts("arch",raw,expected)
                    self.accepts("arch",raw,projection,output="projection")
                    summary=json.loads(self.accepts("arch",raw,output="summary"))
                    self.assertEqual(summary["id"],identity)
                    self.assertEqual(summary["raw_digest"],raw_digest)
                print("EXCHANGE_SCALE "+json.dumps({"axis":axis,"payload_bytes":length,
                    "input_bytes":len(raw),"canonical_bytes":len(expected),"input_sha256":raw_digest,
                    "semantic_id":identity,"repeats":2,
                    "elapsed_seconds":round(time.monotonic()-started,6)},sort_keys=True))
        doc=fixture();doc["annotations"]["golden.example/review"]="x"*65537
        self.rejects("arch",doc,"limit",path=["annotations","golden.example/review"])
        doc=fixture();doc["body"]["provenance"]["display"]="x"*1025
        self.rejects("arch",doc,"semantic",core="limit")
