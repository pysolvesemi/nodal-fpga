"""Cross-envelope parser/compatibility controls; no production-derived oracle."""
import copy
import json
from support import ExchangeCLI, at, encoded, fixture
from test_package_design import bound_package


def duplicate_at(value, target, path=()):
    """Encode one repeated decoded key, retaining otherwise valid full input."""
    if isinstance(value, dict):
        fields=[]
        first=next(iter(value), None)
        for key,item in value.items():
            part=encoded(key)+b":"+duplicate_at(item,target,path+(key,))
            fields.append(part)
            if path==tuple(target) and key==first:
                # JSON-equivalent spelling is exercised separately by parser
                # literals; this exact duplicate is located at every object site.
                fields.append(part)
        return b"{"+b",".join(fields)+b"}"
    if isinstance(value,list):
        return b"["+b",".join(duplicate_at(v,target,path+(i,)) for i,v in enumerate(value))+b"]"
    return encoded(value)


def objects(value,path=()):
    if isinstance(value,dict):
        if value:yield path
        for key,item in value.items():yield from objects(item,path+(key,))
    elif isinstance(value,list):
        for i,item in enumerate(value):yield from objects(item,path+(i,))


class CommonEnvelopeConformance(ExchangeCLI):
    def test_full_package_and_design_duplicate_keys_at_every_object_site(self):
        bound,artifacts=bound_package()
        for operation,doc,supplied in [("package",fixture("package"),None),
                                       ("package",bound,artifacts),("design",fixture("design"),None)]:
            options={"artifacts":supplied}
            if operation=="design":options["package"]=fixture("package")
            for path in objects(doc):
                with self.subTest(operation=operation,path=path):
                    first=next(iter(at(doc,path)))
                    self.rejects(operation,duplicate_at(doc,path),"duplicate_key",path=list(path)+[first],**options)

    def test_compatibility_failure_precedes_malformed_body_for_each_format(self):
        for operation,name in [("arch","architecture"),("package","package"),("design","design")]:
            options={"package":fixture("package")} if operation=="design" else {}
            for path,value,code in [(["format"],"future.format","unsupported_format"),
                (["version","minor"],2,"unsupported_version"),(["profile","revision"],2,"unsupported_profile"),
                (["required_features",0,"id"],"future.example/semantic","unsupported_feature")]:
                doc=fixture(name);at(doc,path[:-1])[path[-1]]=value;doc["body"]=False
                self.rejects(operation,doc,code,path=path,**options)
            doc=fixture(name);doc["required_features"]=[];doc["body"]=False
            self.rejects(operation,doc,"missing_feature",path=["required_features"],**options)
            doc=fixture(name);doc["required_features"].append(copy.deepcopy(doc["required_features"][0]))
            doc["body"]=False
            self.rejects(operation,doc,"duplicate_feature",path=["required_features",1],**options)

    def test_full_envelope_depth_counts_root_annotation_container_overhead(self):
        # Root plus annotations object already consume 2 levels. A scalar leaf
        # adds none. This distinguishes envelope depth from pure-parser probes.
        for shape in ["array","object","mixed"]:
            for levels in [62,63]:
                value=0
                for i in range(levels):
                    value=[value] if shape=="array" or (shape=="mixed" and i%2) else {"x":value}
                doc=fixture();doc["annotations"]["golden.example/review"]=value
                if levels==62:self.accepts("arch",doc,encoded(doc))
                else:self.rejects("arch",doc,"limit")
