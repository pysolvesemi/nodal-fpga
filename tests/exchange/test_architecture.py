"""Strict envelope/type compatibility and architecture identity conformance."""
import copy
import json
from support import (ALGORITHM, GOLDENS, ExchangeCLI, P0, architecture_projection,
                     at, changed, encoded, fixture, pointer, resign_architecture)


# One independently selected representative of every architecture record shape.
RECORDS = [
    [], ["version"], ["profile"], ["required_features",0], ["optional_features",0],
    ["body"], ["body","provenance"], ["body","provenance","span"],
    ["body","resource_types",0], ["body","resource_types",0,"key"],
    ["body","resource_types",0,"pins",0], ["body","domains",0],
    ["body","roots",0], ["body","roots",0,"domains",0], ["body","templates",0],
    ["body","templates",0,"resources",0], ["body","templates",0,"mode_groups",0],
    ["body","templates",0,"mode_groups",0,"resources",0], ["body","templates",0,"storage",0],
    ["body","templates",0,"features",0], ["body","templates",0,"features",0,"range"],
    ["body","templates",0,"features",0,"domain"], ["body","templates",0,"connections",0],
    ["body","templates",0,"connections",0,"destination"],
    ["body","templates",0,"connections",0,"selector"],
]


class ArchitectureConformance(ExchangeCLI):
    def test_every_valid_literal_full_architecture(self):
        for name in ["architecture", "architecture-hierarchy", "architecture-alias", "architecture-high-u64",
                     "architecture-mux-reversed", "architecture-pins-reversed", "architecture-cold-edit"]:
            with self.subTest(name=name):
                raw=(GOLDENS/(name+".raw.json")).read_bytes()
                canonical=(GOLDENS/(name+".canonical.json")).read_bytes()
                projection=(GOLDENS/(name+".projection.json")).read_bytes()
                self.accepts("arch",raw,canonical)
                self.accepts("arch",raw,projection,output="projection")
                self.accepts("arch",canonical,canonical)  # Supported second-read round trip.
                summary=json.loads(self.accepts("arch",raw,output="summary"))
                self.assertEqual(summary["id"],json.loads(canonical)["body"]["semantic_id"])
                self.assertEqual([n["code"] for n in summary["notices"]],["unknown_annotation"])

    def test_independent_dynamic_projection_matches_fixed_goldens(self):
        # Guards the test input builder itself against drifting into a different
        # projection before it is used for scale or deliberate semantic variants.
        for name in ["architecture","architecture-alias","architecture-hierarchy","architecture-high-u64"]:
            with self.subTest(name=name):
                self.assertEqual(encoded(architecture_projection(fixture(name))),
                                 (GOLDENS/(name+".projection.json")).read_bytes())

    def test_focused_guard_resource_alias_and_range_domain_inputs(self):
        for name in ["guarded-alias","resource-alias","range-domain"]:
            data=(GOLDENS.parent/"semantic-cases"/(name+".json")).read_bytes()
            self.accepts("arch",data,data)
        data=json.loads((GOLDENS.parent/"semantic-cases/guarded-alias.json").read_bytes())
        path=["body","templates",0,"features",0,"guard",0]
        unknown=copy.deepcopy(data);at(unknown,path)["extra"]=0
        self.rejects("arch",unknown,"unknown_field",path=path+["extra"])
        for member in at(data,path):
            missing=copy.deepcopy(data);del at(missing,path)[member]
            self.rejects("arch",missing,"missing_field",path=path+[member])
        duplicate=copy.deepcopy(data);duplicate["body"]["templates"][0]["features"][0]["guard"].append(copy.deepcopy(at(data,path)))
        self.rejects("arch",duplicate,"semantic",core="guard")
        primary=fixture()["body"]["semantic_id"]
        ranged=json.loads((GOLDENS.parent/"semantic-cases/range-domain.json").read_bytes())
        self.assertNotEqual(ranged["body"]["semantic_id"],primary)

    def test_each_semantic_record_rejects_duplicate_decoded_keys(self):
        base=fixture()
        def emit(value,target,path=()):
            if isinstance(value,dict):
                fields=[]
                for key in sorted(value):
                    field=encoded(key)+b":"+emit(value[key],target,path+(key,))
                    fields.append(field)
                    if path==tuple(target) and key==sorted(value)[0]:
                        fields.append(field)
                return b"{"+b",".join(fields)+b"}"
            if isinstance(value,list):
                return b"["+b",".join(emit(v,target,path+(i,)) for i,v in enumerate(value))+b"]"
            return encoded(value)
        for path in RECORDS:
            with self.subTest(path=path):
                member=sorted(at(base,path))[0]
                self.rejects("arch",emit(base,path),"duplicate_key",path=path+[member])

    def test_keyed_declaration_permutations_preserve_exact_output(self):
        expected=(GOLDENS/"architecture.canonical.json").read_bytes()
        for name in ["architecture-root-permuted.raw.json","architecture-set-permuted.raw.json"]:
            self.accepts("arch",(GOLDENS/name).read_bytes(),expected)
        doc=fixture()
        doc["body"]["templates"][0]["resources"].reverse()
        doc["body"]["domains"].reverse()
        doc["body"]["connections"].reverse()
        for root in doc["body"]["roots"]:
            root["domains"].reverse()
        self.accepts("arch",doc,expected)

    def test_semantic_numeric_sets_sort_by_magnitude_not_decimal_text(self):
        doc=fixture("architecture-alias")
        doc["body"]["partitions"]=["0","2","10"]
        template=doc["body"]["templates"][0]
        template["storage"][0]["bits"]="4"
        for feature in template["features"]:
            feature["width"]="4";feature["range"]["length"]="4"
            feature["domain"]={"kind":"set","values":["0","2","10"]}
        expected=resign_architecture(doc)
        permuted=copy.deepcopy(expected);permuted["body"]["partitions"]=["10","2","0"]
        for feature in permuted["body"]["templates"][0]["features"]:
            feature["domain"]["values"]=["10","0","2"]
        self.accepts("arch",permuted,encoded(expected))

    def test_every_semantic_object_is_closed(self):
        base=fixture()
        for path in RECORDS:
            with self.subTest(path=path):
                doc=copy.deepcopy(base)
                at(doc,path)["unexpected"]=0
                self.rejects("arch",doc,"unknown_field",path=path+["unexpected"])
        # Unknown fields inside annotations are allowed data, outside it are not.
        doc=fixture();doc["annotations"]["golden.example/review"]["new-data"]={"arbitrary":[None,True,-1]}
        accepted=json.loads(self.accepts("arch",doc))
        self.assertEqual(accepted["annotations"],doc["annotations"])
        self.rejects("arch",changed(base,["annotations2"],{}),"unknown_field",path=["annotations2"])

    def test_unknown_key_pointer_preserves_backtick_slash_and_tilde(self):
        for parent in [[], ["body"], ["body", "templates", 0, "resources", 0]]:
            doc=fixture();at(doc,parent)["a`b/~"]=0
            self.rejects("arch",doc,"unknown_field",path=parent+["a`b/~"])

    def test_schema_fail_fast_follows_input_member_order(self):
        # Intentionally bypass encoded(), whose object sorting is appropriate for
        # canonical expectations but would destroy these input-order controls.
        def input_bytes(doc):
            return json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode()
        rt_path=["body","resource_types",0]
        original=at(fixture(),rt_path)
        for first,second,expected in [
            (("kind","bad"),("key",dict(original["key"],kind="bad")),rt_path+["kind"]),
            (("key",dict(original["key"],kind="bad")),("kind","bad"),rt_path+["key","kind"])]:
            doc=fixture();record=dict([first,second])
            record.update({k:v for k,v in original.items() if k not in record})
            doc["body"]["resource_types"][0]=record
            self.rejects("arch",input_bytes(doc),"invalid_enum",path=expected)
        key_path=rt_path+["key"]
        original=at(fixture(),key_path)
        for pairs,code,field in [([("kind","bad"),("local",False)],"invalid_enum","kind"),
                                ([("local",False),("kind","bad")],"wrong_type","local")]:
            doc=fixture();key=dict(pairs);key.update({k:v for k,v in original.items() if k not in key})
            at(doc,rt_path)["key"]=key
            self.rejects("arch",input_bytes(doc),code,path=key_path+[field])
        pin_path=rt_path+["pins",0];original=at(fixture(),pin_path)
        for pairs,code,field in [([("unknown",0),("width",False)],"unknown_field","unknown"),
                                ([("width",False),("unknown",0)],"wrong_type","width")]:
            doc=fixture();pin=dict(pairs);pin.update({k:v for k,v in original.items() if k not in pin})
            at(doc,rt_path)["pins"][0]=pin
            self.rejects("arch",input_bytes(doc),code,path=pin_path+[field])

    def test_untrusted_enum_error_markers_cannot_override_category(self):
        for token in ["[overflow]","[invalid_unsigned]","[wrong_type]","[unknown_field]"]:
            for path in [["body","resource_types",0,"kind"],
                         ["body","resource_types",0,"key","kind"],
                         ["body","resource_types",0,"pins",0,"direction"],
                         ["body","templates",0,"features",0,"domain","kind"]]:
                self.rejects("arch",changed(fixture(),path,token),"invalid_enum",path=path)

    def test_unknown_optional_in_project_namespace_is_preserved(self):
        doc=fixture();doc["optional_features"].append({"id":"nodal-fpga/note","revision":1})
        doc["annotations"]["nodal-fpga/note"]={"semantic_id":"cold data","provenance":[1,2]}
        self.accepts("arch",doc,encoded(doc))
        summary=json.loads(self.accepts("arch",doc,output="summary"))
        self.assertEqual(summary["id"],fixture()["body"]["semantic_id"])
        self.assertEqual([n["code"] for n in summary["notices"]],["unknown_annotation","unknown_annotation"])

    def test_unknown_member_equal_to_parent_token_is_not_collapsed(self):
        doc=fixture();doc["body"]["templates"][0]["features"][0]["domain"]={"kind":"any","domain":0}
        self.rejects("arch",doc,"unknown_field",path=["body","templates",0,"features",0,"domain","domain"])

    def test_partition_narrowing_respects_input_order_before_bad_name_type(self):
        for pairs,code,field in [([("partition","4294967296"),("name",False)],"overflow","partition"),
                                ([("name",False),("partition","4294967296")],"wrong_type","name")]:
            doc=fixture();original=doc["body"]["roots"][0]
            root=dict(pairs);root.update({k:v for k,v in original.items() if k not in root})
            doc["body"]["roots"][0]=root
            raw=json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode()
            self.rejects("arch",raw,code,path=["body","roots",0,field])

    def test_long_unknown_key_exact_pointer_and_bounded_presentation(self):
        key="é"*1000+"a`b/~"
        doc=fixture();doc["body"][key]=0
        error=self.rejects("arch",doc,"unknown_field",path=["body",key])
        for field in ["message","actual","expected"]:
            if error.get(field) is not None:
                self.assertLessEqual(len(error[field].encode("utf-8")),1024)
        self.assertNotIn(key,error["message"])

    def test_digest_grammar_and_capability_identifier_grammar(self):
        for value in ["", "a"*63, "a"*65, "A"*64, "g"*64]:
            self.rejects("arch",changed(fixture(),["body","semantic_id"],value),
                         "identity_mismatch",stage="decode",path=["body","semantic_id"])
        for value in ["NoNamespace","bad_namespace/name","valid.example/Bad","valid.example/"]:
            self.rejects("arch",changed(fixture(),["required_features",0,"id"],value),
                         "invalid_annotation",stage="envelope",path=["required_features",0,"id"])

    def test_all_required_fields_remain_required_including_nullable(self):
        base=fixture()
        for path in RECORDS:
            for member in at(base,path):
                with self.subTest(path=path,member=member):
                    doc=copy.deepcopy(base)
                    del at(doc,path)[member]
                    self.rejects("arch",doc,"missing_field",path=path+[member])

    def test_nullable_fields_do_not_turn_absent_into_null(self):
        cases=[(["body","templates",0,"resources",0,"alias_of"],None),
               (["body","templates",0,"features",0,"alias_of"],None),
               (["body","connections",0,"selector"],None),
               (["body","resource_types",0,"provenance","span"],None),
               (["body","resource_types",0,"provenance","display"],None)]
        for path,value in cases:
            self.assertIs(at(fixture(),path),value)
            self.rejects("arch",changed(fixture(),path,False),"wrong_type",path=path)
        hierarchy=fixture("architecture-hierarchy")
        path=["body","templates",1,"children",0,"partition"]
        self.assertIs(at(hierarchy,path),None)
        self.rejects("arch",changed(hierarchy,path,False),"wrong_type",path=path)
        absent=copy.deepcopy(hierarchy);del at(absent,path[:-1])[path[-1]]
        self.rejects("arch",absent,"missing_field",path=path)
        # Null is explicit data but not legal at a root partition.
        self.rejects("arch",changed(fixture(),["body","roots",0,"partition"],None),"semantic",core="partition_mismatch")

    def test_incomplete_algorithm_envelopes_are_not_valid_architectures(self):
        self.rejects("arch",(ALGORITHM/"C25.json").read_bytes(),"missing_feature",path=["required_features"])
        for name in ["C26.json","C27.json"]:
            self.rejects("arch",(ALGORITHM/name).read_bytes(),"unsupported_format",path=["format"])

    def test_exact_kind_version_profile_and_required_capabilities(self):
        cases=[(["format"],"nodal-fpga.mapped-design","unsupported_format"),
               (["version","major"],1,"unsupported_version"),(["version","minor"],2,"unsupported_version"),
               (["profile","id"],"future-profile","unsupported_profile"),(["profile","revision"],2,"unsupported_profile"),
               (["required_features",0,"id"],"unknown.example/feature","unsupported_feature"),
               (["required_features",0,"revision"],2,"unsupported_feature")]
        for path,value,code in cases:
            with self.subTest(path=path,value=value):
                self.rejects("arch",changed(fixture(),path,value),code,path=path)
        doc=fixture();doc["required_features"]=[]
        self.rejects("arch",doc,"missing_feature",path=["required_features"])
        for revision in [1,2]:
            doc=fixture();duplicate=copy.deepcopy(doc["required_features"][0]);duplicate["revision"]=revision
            doc["required_features"].append(duplicate)
            self.rejects("arch",doc,"duplicate_feature",path=["required_features",1])
        doc=fixture();doc["optional_features"].append(copy.deepcopy(doc["required_features"][0]))
        self.rejects("arch",doc,"unsupported_feature",path=["optional_features",1])

    def test_annotations_are_bounded_nonsemantic_declared_data(self):
        doc=fixture();doc["annotations"]["golden.example/review"]=[None,True,False,"é",-2147483648,2147483647,{"nested":"value"}]
        result=json.loads(self.accepts("arch",doc))
        self.assertEqual(result["annotations"],doc["annotations"])
        self.assertEqual(result["body"]["semantic_id"],doc["body"]["semantic_id"])
        doc=fixture();doc["annotations"]={}
        self.accepts("arch",doc)  # Optional declaration with no data is allowed.
        doc=fixture();doc["optional_features"]=[]
        self.rejects("arch",doc,"invalid_annotation",path=["annotations","golden.example/review"])
        for value in [-2147483649,2147483648]:
            doc=fixture();doc["annotations"]["golden.example/review"]=value
            self.rejects("arch",doc,"overflow")
        for raw in [b'-0',b'1.0',b'1e0']:
            original=encoded(fixture())
            data=original.replace(b'"count":3',b'"count":'+raw)
            self.assertNotEqual(data,original)
            self.rejects("arch",data,"invalid_json")

    def test_semantic_unsigned_types_grammar_and_overflow(self):
        path=["body","templates",0,"storage",0,"bits"]
        for value in [0,True,None,{},[]]:
            with self.subTest(value=value):
                self.rejects("arch",changed(fixture(),path,value),"wrong_type",path=path)
        for value in ["","00","01","+1","-0","-1"," 1","1 ","1.0","1e0","1E+0","0x1","１","١","1\n","1\t"]:
            with self.subTest(value=value):
                self.rejects("arch",changed(fixture(),path,value),"invalid_unsigned",path=path)
        self.rejects("arch",changed(fixture(),path,"18446744073709551616"),"overflow",path=path)
        self.rejects("arch",changed(fixture(),["body","roots",0,"partition"],"4294967296"),"overflow",path=["body","roots",0,"partition"])
        # Escaping decimal digits changes input spelling only, not decoded value.
        raw=(GOLDENS/"architecture.canonical.json").read_bytes()
        escaped=raw.replace(b'"bits":"2"',b'"bits":"\\u0032"')
        self.assertNotEqual(raw,escaped)
        self.accepts("arch",escaped,raw)

    def test_full_exact_u64_storage_boundaries(self):
        for value in ["9007199254740991","9007199254740992","9007199254740993","9223372036854775808","18446744073709551615"]:
            with self.subTest(value=value):
                doc=fixture("architecture-high-u64")
                doc["body"]["templates"][0]["storage"][0]["bits"]=value
                doc["body"]["templates"][0]["features"][0]["range"]["start"]=str(int(value)-1)
                doc=resign_architecture(doc)
                result=json.loads(self.accepts("arch",doc,encoded(doc)))
                self.assertEqual(result["body"]["templates"][0]["storage"][0]["bits"],value)
        doc=fixture("architecture-high-u64")
        doc["body"]["templates"][0]["features"][0]["range"]["start"]="18446744073709551615"
        self.rejects("arch",doc,"semantic",core="overflow")

    def test_metadata_integer_types_ranges_and_lexemes(self):
        for value in ["1",True,None]:
            self.rejects("arch",changed(fixture(),["version","minor"],value),"wrong_type",path=["version","minor"])
        for value in [-1,65536]:
            self.rejects("arch",changed(fixture(),["version","minor"],value),"overflow",path=["version","minor"])
        raw=encoded(fixture())
        for token in [b'-0',b'0.0',b'0e0']:
            self.rejects("arch",raw.replace(b'"major":0',b'"major":'+token),"invalid_json")

    def test_provenance_bounds_are_not_semantic_identity(self):
        path=["body","provenance","display"]
        doc=changed(fixture(),path,"é"*512)
        result=json.loads(self.accepts("arch",doc))
        self.assertEqual(result["body"]["semantic_id"],fixture()["body"]["semantic_id"])
        self.rejects("arch",changed(doc,path,"é"*512+"a"),"semantic",core="limit")
        self.rejects("arch",changed(fixture(),["body","provenance","span","end"],"513"),"semantic",core="bounds")
        self.rejects("arch",changed(fixture(),["body","provenance","span","start"],"513"),"semantic",core="invalid_range")

    def test_alias_and_mux_contract_mutations_keep_intended_categories(self):
        alias=fixture("architecture-alias")
        mismatch=copy.deepcopy(alias)
        mismatch["body"]["templates"][0]["features"][1]["width"]="1"
        mismatch["body"]["templates"][0]["features"][1]["range"]["length"]="1"
        self.rejects("arch",mismatch,"semantic",core="alias_mismatch")
        chain=copy.deepcopy(alias);extra=copy.deepcopy(chain["body"]["templates"][0]["features"][1])
        extra["name"]="zz-alias";extra["alias_of"]["name"]="alias"
        chain["body"]["templates"][0]["features"].append(extra)
        self.rejects("arch",chain,"semantic",core="alias_chain")
        cycle=copy.deepcopy(alias)
        cycle["body"]["templates"][0]["features"][0]["alias_of"]={"name":"alias","path":[],"provenance":copy.deepcopy(P0)}
        self.rejects("arch",cycle,"semantic",core="alias_cycle")
        reserved=fixture();reserved["body"]["templates"][0]["features"][0]["domain"]={"kind":"any"}
        self.rejects("arch",reserved,"semantic",core="domain")

    def test_structural_negative_categories_and_late_identity(self):
        for width in ["0","65"]:
            self.rejects("arch",changed(fixture(),["body","templates",0,"features",0,"width"],width),"semantic",core="width")
        doc=fixture();doc["body"]["roots"].append(copy.deepcopy(doc["body"]["roots"][0]))
        self.rejects("arch",doc,"semantic",core="duplicate")
        doc=fixture();doc["body"]["templates"][0]["features"][0]["domain"]["values"]=["0","1","1","2"]
        self.rejects("arch",doc,"semantic",core="domain")
        doc=fixture();doc["body"]["templates"][0]["connections"][0]["sources"][0]["pin"]="I"
        self.rejects("arch",doc,"semantic",core="direction")
        doc=fixture();doc["body"]["templates"][0]["children"]=[{"name":"self","template":copy.deepcopy(doc["body"]["templates"][0]["key"]),"partition":None,"domains":[],"provenance":copy.deepcopy(P0)}]
        self.rejects("arch",doc,"semantic",core="template_cycle")
        self.rejects("arch",changed(fixture(),["body","semantic_id"],"0"*64),"identity_mismatch",path=["body","semantic_id"])
        self.rejects("arch",fixture(),"semantic",core="limit",limits={"core":{"max_work":1}})

    def test_independent_core_budget_axes_are_enforced(self):
        for field,value in [("max_declarations",1),("max_references",1),("max_collection",1),
                            ("max_key_component_bytes",1),("max_key_bytes",1),("max_provenance_bytes",1)]:
            with self.subTest(field=field):
                self.rejects("arch",fixture(),"semantic",core="limit",limits={"core":{field:value}})
        self.rejects("arch",fixture("architecture-hierarchy"),"semantic",core="limit",limits={"core":{"max_depth":1}})

    def test_sparse_hole_and_routing_cycle_are_independently_distinguished(self):
        doc=fixture();doc["body"]["roots"]=[doc["body"]["roots"][0],doc["body"]["roots"][2]]
        self.rejects("arch",doc,"semantic",core="missing")
        doc["body"]["connections"]=[]
        doc=resign_architecture(doc)
        result=json.loads(self.accepts("arch",doc,encoded(doc)))
        self.assertEqual([r["name"] for r in result["body"]["roots"]],["t0","t2"])
        self.assertEqual(result["body"]["connections"],[])
        cycle=fixture();edge=copy.deepcopy(cycle["body"]["connections"][0]);edge["name"]="edge2"
        edge["sources"][0]["resource"]["path"]=["t2"];edge["destination"]["resource"]["path"]=["t0"]
        cycle["body"]["connections"].append(edge);cycle=resign_architecture(cycle)
        self.accepts("arch",cycle,encoded(cycle))
