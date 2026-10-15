"""Exact package integrity, flat artifact boundaries and target-bound design tests."""
import copy
import hashlib
import json
from support import (GOLDENS, ExchangeCLI, at, changed, encoded, fixture,
                     package_projection, resign_architecture, resign_design, resign_package)

RAW=(GOLDENS/"architecture.raw.json").read_bytes()
RAW_SHA=hashlib.sha256(RAW).hexdigest()


def artifact(data):
    return {"bytes":str(len(data)),"sha256":hashlib.sha256(data).hexdigest()}


def bound_package():
    # This opaque leaf is deliberately not a valid envelope and must never be
    # interpreted for URLs, nested dependency resolution or executable behavior.
    content=b'{"format":"nodal-fpga.package-manifest","url":"https://example.invalid/never-fetch","nested":{"design":"not executable"}}'
    descriptor=artifact(content)
    doc=fixture("package")
    doc["body"]["libraries"]=[{"id":"inline-extra","revision":"1","artifact":copy.deepcopy(descriptor)}]
    doc["body"]["configuration_map"]={"state":"bound","revision":"opaque-test","artifact":copy.deepcopy(descriptor)}
    doc["body"]["authoring"]={"state":"bound","id":"independent-fixture-identity","version":"1",
        "implementation_sha256":hashlib.sha256(b"identity-only fixture, never executed").hexdigest(),
        "options":[{"name":"alpha","value":"one"},{"name":"beta","value":"two"}]}
    return resign_package(doc),[(RAW_SHA,RAW),(descriptor["sha256"],content)]


class PackageConformance(ExchangeCLI):
    def test_primary_package_and_immutable_roundtrip(self):
        raw=(GOLDENS/"package.raw.json").read_bytes()
        expected=(GOLDENS/"package.canonical.json").read_bytes()
        self.accepts("package",raw,expected)
        self.accepts("package",raw,(GOLDENS/"package.projection.json").read_bytes(),output="projection")
        self.accepts("package",expected,expected)
        self.assertEqual(encoded(package_projection(fixture("package"))),
                         (GOLDENS/"package.projection.json").read_bytes())
        summary=json.loads(self.accepts("package",raw,output="summary"))
        self.assertEqual(summary["id"],fixture("package")["body"]["build_id"])
        self.assertEqual(summary["architecture"]["id"],fixture()["body"]["semantic_id"])

    def test_raw_integrity_precedes_architecture_semantics(self):
        package=fixture("package")
        corrupt=b'!'+RAW[1:]
        self.rejects("package",package,"artifact_digest",artifacts=[(RAW_SHA,corrupt)])
        self.rejects("package",package,"artifact_length",artifacts=[(RAW_SHA,RAW[:-1])])
        self.rejects("package",package,"artifact_length",artifacts=[(RAW_SHA,RAW+b' ')])
        self.rejects("package",package,"artifact_missing",artifacts=[])
        # Equal decoded architecture is insufficient for exact artifact binding.
        self.rejects("package",package,"artifact_length",artifacts=[(RAW_SHA,(GOLDENS/"architecture.canonical.json").read_bytes())])
        self.rejects("package",changed(package,["body","build_id"],"0"*64),"identity_mismatch",path=["body","build_id"],artifacts=[])

    def test_correct_raw_digest_cannot_hide_wrong_architecture_kind(self):
        data=(GOLDENS/"design.canonical.json").read_bytes()
        package=fixture("package");package["body"]["architecture"]["artifact"]=artifact(data)
        package=resign_package(package)
        self.rejects("package",package,"unsupported_format",artifacts=[(artifact(data)["sha256"],data)])

    def test_manifest_schema_unknown_fields_required_fields_and_nulls(self):
        base=fixture("package")
        paths=[[],["body"],["body","architecture"],["body","architecture","artifact"],
               ["body","authoring"],["body","device_db"],["body","macro_bindings"]]
        bound,artifacts=bound_package()
        for doc,records,supplied in [(base,paths,None),(bound,[["body","libraries",0],
            ["body","libraries",0,"artifact"],["body","authoring"],["body","authoring","options",0],
            ["body","configuration_map"]],artifacts)]:
            for path in records:
                changed_doc=copy.deepcopy(doc);at(changed_doc,path)["unexpected"]=0
                self.rejects("package",changed_doc,"unknown_field",path=path+["unexpected"],artifacts=supplied)
                for member in at(doc,path):
                    with self.subTest(path=path,member=member):
                        changed_doc=copy.deepcopy(doc);del at(changed_doc,path)[member]
                        self.rejects("package",changed_doc,"missing_field",path=path+[member],artifacts=supplied)
        for role in ["authoring","compiler","backend","device_db","physical_implementation","technology",
                     "macro_bindings","configuration_map","transport","activation","timing_datasets","external_pin_map"]:
            self.rejects("package",changed(base,["body",role],None),"wrong_type",path=["body",role])
        # No design role exists in the manifest; opaque lookalike bytes cannot add it.
        doc=fixture("package");doc["body"]["mapped_design"]={}
        self.rejects("package",doc,"unknown_field",path=["body","mapped_design"])

    def test_hostile_decoded_unknown_keys_have_exact_nested_pointers(self):
        package,artifacts=bound_package()
        for path in [[],["body","authoring"],["body","authoring","options",0],
                     ["body","configuration_map"],["body","libraries",0,"artifact"]]:
            for key in ["a`b/~", "é"*1000+"a`b/~"]:
                doc=copy.deepcopy(package);at(doc,path)[key]=0
                raw=encoded(doc).replace(b'"a`b/~":', b'"\\u0061\\u0060b\\u002f\\u007e":')
                error=self.rejects("package",raw,"unknown_field",path=path+[key],artifacts=artifacts)
                for field in ["message","actual","expected"]:
                    if error.get(field) is not None:
                        self.assertLessEqual(len(error[field].encode("utf-8")),1024)
                if len(key)>1024:
                    self.assertNotIn(key,error["message"])

    def test_untrusted_tag_markers_and_nested_option_input_order(self):
        base,artifacts=bound_package()
        for token in ["[overflow]","[invalid_unsigned]"]:
            self.rejects("package",changed(base,["body","authoring","state"],token),
                         "invalid_enum",path=["body","authoring","state"],artifacts=artifacts)
        for first,second in [("name","value"),("value","name")]:
            doc=copy.deepcopy(base)
            doc["body"]["authoring"]["options"][0]={first:False,second:False}
            raw=json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode()
            self.rejects("package",raw,"wrong_type",path=["body","authoring","options",0,first],artifacts=artifacts)

    def test_unknown_member_equal_to_parent_binding_name_is_not_collapsed(self):
        doc=fixture("package");doc["body"]["authoring"]["authoring"]=0
        self.rejects("package",doc,"unknown_field",path=["body","authoring","authoring"])

    def test_all_opaque_roles_bound_do_not_activate_unsupported_operations(self):
        doc,artifacts=bound_package()
        for role in ["compiler","backend"]:
            doc["body"][role]=copy.deepcopy(doc["body"]["authoring"])
        for role in ["device_db","physical_implementation","technology","macro_bindings",
                     "transport","activation","timing_datasets","external_pin_map"]:
            doc["body"][role]=copy.deepcopy(doc["body"]["configuration_map"])
        doc=resign_package(doc)
        self.accepts("package",doc,encoded(doc),artifacts=artifacts)
        for operation in ["rtl","device-query","route","program","timing"]:
            self.rejects(operation,doc,"unsupported_operation",artifacts=artifacts)

    def test_flat_opaque_leaf_and_reused_digest_are_accepted(self):
        package,artifacts=bound_package()
        # Same opaque digest referenced by a library and a view. Only this leaf and
        # the architecture may be resolved; Rust public API tests count the calls.
        self.accepts("package",package,encoded(package),artifacts=artifacts)
        self.assertEqual(len(artifacts),2)
        reordered=copy.deepcopy(package);reordered["body"]["authoring"]["options"].reverse()
        self.accepts("package",reordered,encoded(package),artifacts=artifacts)

    def test_conflicting_descriptor_lengths_and_keyed_record_duplicates(self):
        raw=(GOLDENS.parent/"package-cases/conflicting-length.json").read_bytes()
        self.rejects("package",raw,"artifact_length",path=["body","libraries",0,"artifact","bytes"],artifacts=[])
        package,artifacts=bound_package()
        for path in [["body","libraries"],["body","authoring","options"]]:
            doc=copy.deepcopy(package);at(doc,path).append(copy.deepcopy(at(doc,path)[0]))
            self.rejects("package",doc,"duplicate",path=path+[len(at(doc,path))-1],artifacts=[])

    def test_declared_and_actual_aggregate_limits_include_architecture_once(self):
        package=fixture("package")
        self.accepts("package",package,encoded(package),limits={"artifacts":1,"artifact_bytes":len(RAW)})
        self.rejects("package",package,"limit",limits={"artifact_bytes":len(RAW)-1},artifacts=[])
        bound,artifacts=bound_package()
        self.rejects("package",bound,"limit",limits={"artifacts":1},artifacts=[])
        extra=len(artifacts[1][1])
        self.accepts("package",bound,encoded(bound),artifacts=artifacts,
                     limits={"artifacts":2,"artifact_bytes":len(RAW)+extra})
        self.rejects("package",bound,"limit",limits={"artifact_bytes":len(RAW)+extra-1},artifacts=[])
        # Per-artifact declared ceiling is checked before resolver calls. Its own
        # manifest remains smaller than the lowered input-byte ceiling.
        oversized=fixture("package");oversized["body"]["libraries"]=[{"id":"oversized","revision":"1",
            "artifact":{"bytes":"6625","sha256":"1"*64}}]
        oversized=resign_package(oversized)
        self.rejects("package",oversized,"limit",limits={"input_bytes":6624},artifacts=[])

    def test_self_id_and_dependency_changes_are_not_excluded(self):
        package,artifacts=bound_package()
        stale=copy.deepcopy(package);stale["body"]["configuration_map"]["revision"]="different"
        self.rejects("package",stale,"identity_mismatch",path=["body","build_id"],artifacts=[])
        fresh=resign_package(stale)
        self.assertNotEqual(fresh["body"]["build_id"],package["body"]["build_id"])
        self.accepts("package",fresh,encoded(fresh),artifacts=artifacts)
        cold=(GOLDENS/"architecture-cold-edit.raw.json").read_bytes()
        self.accepts("package",(GOLDENS/"package-cold-edit.raw.json").read_bytes(),
                     (GOLDENS/"package-cold-edit.canonical.json").read_bytes(),
                     artifacts=[(hashlib.sha256(cold).hexdigest(),cold)])

    def test_no_unsupported_operation_or_implicit_migration(self):
        for operation in ["rtl","device-query","route","program","timing","migrate"]:
            with self.subTest(operation=operation):
                self.rejects(operation,(GOLDENS/"package.raw.json").read_bytes(),"unsupported_operation")


class DesignConformance(ExchangeCLI):
    def invoke_design(self,data,**kwargs):
        return self.accepts("design",data,package=(GOLDENS/"package.raw.json").read_bytes(),**kwargs)

    def reject_design(self,data,code,**kwargs):
        return self.rejects("design",data,code,package=(GOLDENS/"package.raw.json").read_bytes(),**kwargs)

    def test_literal_target_bound_design_and_roundtrip(self):
        canonical=(GOLDENS/"design.canonical.json").read_bytes()
        self.invoke_design((GOLDENS/"design.raw.json").read_bytes(),expected=canonical)
        self.invoke_design(canonical,expected=canonical)
        self.invoke_design(canonical,expected=(GOLDENS/"design.projection.json").read_bytes(),output="projection")
        body=json.loads(canonical)["body"]
        self.assertEqual(len(body["cells"]),2);self.assertEqual(len(body["ports"]),3);self.assertEqual(len(body["nets"]),4)
        self.assertEqual(body["nets"][1]["loads"][0]["cell"],"c1")
        self.assertEqual(body["nets"][1]["loads"][1]["port"],"out")
        self.assertEqual(body["nets"][3]["driver"],{"kind":"constant","value":"1","provenance":{"display":None,"span":None}})

    def test_exact_target_precedes_target_lookup(self):
        doc=fixture("design-cold-target")
        self.reject_design(doc,"target_build_mismatch",path=["body","target_build_id"])
        doc["body"]["cells"][0]["resource_type"]["local"]="does-not-exist"
        doc["body"]["nets"][1]["driver"]["pin"]="does-not-exist"
        self.reject_design(doc,"target_build_mismatch",path=["body","target_build_id"])
        cold=(GOLDENS/"architecture-cold-edit.raw.json").read_bytes()
        self.accepts("design",(GOLDENS/"design-cold-target.raw.json").read_bytes(),
            (GOLDENS/"design-cold-target.canonical.json").read_bytes(),
            package=(GOLDENS/"package-cold-edit.raw.json").read_bytes(),artifacts=[(hashlib.sha256(cold).hexdigest(),cold)])

    def test_design_objects_closed_and_all_fields_required(self):
        base=fixture("design")
        paths=[[],["body"],["body","cells",0],["body","ports",0],["body","nets",0],
               ["body","nets",0,"driver"],["body","nets",1,"driver"],["body","nets",3,"driver"]]
        for path in paths:
            doc=copy.deepcopy(base);at(doc,path)["unexpected"]=0
            self.reject_design(doc,"unknown_field",path=path+["unexpected"])
            for name in at(base,path):
                with self.subTest(path=path,member=name):
                    doc=copy.deepcopy(base);del at(doc,path)[name]
                    self.reject_design(doc,"missing_field",path=path+[name])

    def test_hostile_decoded_unknown_keys_on_tagged_design_endpoints(self):
        for path in [[],["body"],["body","cells",0,"resource_type"],
                     ["body","nets",0,"driver"],["body","nets",1,"loads",0]]:
            for key in ["a`b/~", "é"*1000+"a`b/~"]:
                doc=fixture("design");at(doc,path)[key]=0
                raw=encoded(doc).replace(b'"a`b/~":', b'"\\u0061\\u0060b\\u002f\\u007e":')
                error=self.reject_design(raw,"unknown_field",path=path+[key])
                for field in ["message","actual","expected"]:
                    if error.get(field) is not None:
                        self.assertLessEqual(len(error[field].encode("utf-8")),1024)
                if len(key)>1024:
                    self.assertNotIn(key,error["message"])

    def test_tagged_endpoint_payload_preserves_input_order_after_tag_selection(self):
        path=["body","nets",1,"driver"]
        for token in ["[overflow]","[invalid_unsigned]"]:
            self.reject_design(changed(fixture("design"),path+["kind"],token),"invalid_enum",path=path+["kind"])
        for first,second in [("cell","pin"),("pin","cell")]:
            doc=fixture("design");original=at(doc,path)
            # Discriminator is intentionally last: it chooses the variant, then
            # bad payload fields are visited in input order, not lexical order.
            driver={first:False,second:False}
            driver.update({k:v for k,v in original.items() if k not in driver and k!="kind"})
            driver["kind"]=original["kind"];doc["body"]["nets"][1]["driver"]=driver
            raw=json.dumps(doc,ensure_ascii=False,separators=(",",":")).encode()
            self.reject_design(raw,"wrong_type",path=path+[first])

    def test_typed_key_type_mode_pin_and_direction_rejections(self):
        self.reject_design(changed(fixture("design"),["body","cells",0,"resource_type","kind"],"bel"),
                           "invalid_enum",path=["body","cells",0,"resource_type","kind"])
        for path,value,core in [(["body","cells",0,"resource_type","local"],"missing","missing"),
                               (["body","cells",0,"mode"],"missing","mode"),
                               (["body","nets",1,"driver","pin"],"missing","missing"),
                               (["body","nets",1,"driver","pin"],"I","direction"),
                               (["body","nets",0,"driver","port"],"out","direction"),
                               (["body","nets",1,"loads",1,"port"],"in","direction")]:
            with self.subTest(path=path,value=value):
                self.reject_design(changed(fixture("design"),path,value),"semantic",core=core)
        # A declared wire ResourceType is valid architecture, but cannot serve as
        # the BEL primitive type required by a mapped cell (R1).
        arch=fixture("architecture-hierarchy")
        arch["body"]["resource_types"][0]["kind"]="wire"
        arch["body"]["templates"][0]["resources"][0]["kind"]="wire"
        arch["body"]["connections"][0]["sources"][0]["resource"]["kind"]="wire"
        arch["body"]["connections"][0]["destination"]["resource"]["kind"]="wire"
        arch=resign_architecture(arch);raw=encoded(arch)
        package=fixture("package");package["body"]["architecture"]={"semantic_id":arch["body"]["semantic_id"],"artifact":artifact(raw)}
        package=resign_package(package)
        design=fixture("design");design["body"]["target_build_id"]=package["body"]["build_id"];design=resign_design(design)
        self.rejects("design",design,"semantic",core="wrong_kind",package=package,artifacts=[(artifact(raw)["sha256"],raw)])

    def test_endpoint_ownership_and_scalar_bounds(self):
        doc=fixture("design");doc["body"]["nets"][1]["loads"].append(copy.deepcopy(doc["body"]["nets"][1]["loads"][0]))
        self.reject_design(doc,"semantic",core="duplicate")
        doc=fixture("design");doc["body"]["nets"][2]["driver"]=copy.deepcopy(doc["body"]["nets"][1]["driver"])
        self.reject_design(doc,"semantic",core="duplicate")
        doc=fixture("design");doc["body"]["nets"][2]["loads"][0]["bit"]="0"
        self.reject_design(doc,"semantic",core="duplicate")
        self.reject_design(changed(fixture("design"),["body","nets",0,"driver","bit"],"2"),"semantic",core="bounds")
        self.reject_design(changed(fixture("design"),["body","nets",1,"driver","bit"],"1"),"semantic",core="bounds")
        doc=fixture("design");doc["body"]["nets"][0]["loads"][0]=copy.deepcopy(doc["body"]["nets"][3]["driver"])
        self.reject_design(doc,"semantic",core="direction")

    def test_design_self_id_and_keyed_sets(self):
        self.reject_design(changed(fixture("design"),["body","semantic_id"],"0"*64),"identity_mismatch",path=["body","semantic_id"])
        doc=fixture("design");doc["body"]["cells"].reverse();doc["body"]["ports"].reverse();doc["body"]["nets"].reverse()
        for net in doc["body"]["nets"]:net["loads"].reverse()
        self.invoke_design(doc,expected=(GOLDENS/"design.canonical.json").read_bytes())
