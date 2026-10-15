//! Exact supplemental semantic witnesses. Production APIs are DUT only.
use nf_arch_ir::*;
use nf_types::{BitCount,BitOffset,BitRange,Code,Key,Name,PartitionId,Provenance,Width};
fn n(s:&str)->Name {Name::new(s).unwrap()}
fn p()->Provenance {Provenance::new(None,Some("fnd06-independent-witness".into())).unwrap()}
fn key<K:nf_types::ResourceMarker>(s:&str)->Key<K> {Key::new("fnd06",vec![],s).unwrap()}
fn resource(s:&str)->ResourceRef {ResourceRef{path:vec![],name:n(s),kind:ResourceKind::Bel,provenance:p()}}
fn field(s:&str,root:bool)->FieldRef {FieldRef{path:if root {vec![n("t00")]}else{vec![]},name:n(s),provenance:p()}}
fn feature(s:&str,start:u64,width:u64)->Feature {Feature{name:n(s),owner:resource("lut"),storage:n("config"),range:BitRange::new(BitOffset::new(start),BitCount::new(width)).unwrap(),width:Width::new(width).unwrap(),domain:ValueDomain::Any,guard:vec![],alias_of:None,provenance:p()}}
fn base()->Architecture {
 let mut a=Architecture::new(n("fnd06")); a.partitions=vec![PartitionId::new(0)];
 a.resource_types.push(ResourceType{key:key("LUT"),kind:ResourceKind::Bel,pins:vec![
 Pin{name:n("I"),direction:Direction::Input,width:BitCount::new(1),provenance:p()},
 Pin{name:n("O"),direction:Direction::Output,width:BitCount::new(1),provenance:p()}],modes:vec![],provenance:p()});
 let mut t=Template::new(key("Tile"));
 t.resources.push(Resource{name:n("lut"),kind:ResourceKind::Bel,resource_type:key("LUT"),alias_of:None,domains:vec![],provenance:p()});
 t.storage.push(Storage{name:n("config"),owner:resource("lut"),bits:BitCount::new(20),provenance:p()});
 t.features.push(feature("ff",16,1)); t.features.push(feature("source",19,1));
 a.templates.push(t); a.roots.push(Instance{name:n("t00"),template:key("Tile"),partition:Some(PartitionId::new(0)),domains:vec![],provenance:p()}); a
}
fn setting(s:&str,value:u64)->FeatureSetting {FeatureSetting{field:field(s,true),value,provenance:p()}}
fn reject(result:Result<(),Vec<nf_types::Diagnostic>>,code:Code,id:&str) {
 let errors=result.expect_err("intended semantic rejection required");
 assert!(errors.iter().any(|d|d.code==code),"{id}: {errors:?}");
 println!("GENERIC-NEGATIVE {id} {code:?}");
}
#[test]
fn exact_ff_source_alias_conflict_and_overlap() {
 let baseline=base(); let valid=validate_architecture(&baseline,&ValidationLimits::default()).unwrap();
 let selection=Selection{modes:vec![],features:vec![setting("ff",0),setting("source",1)]};
 validate_selection(&valid,&selection).unwrap();
 println!("GENERIC-BASELINE independent-ff-source");
 let mut overlap=baseline.clone(); overlap.templates[0].features[1].range=BitRange::new(BitOffset::new(16),BitCount::new(1)).unwrap();
 reject(validate_architecture(&overlap,&ValidationLimits::default()).map(|_|()),Code::Overlap,"M-FIELD-ALIAS");
 overlap.templates[0].features[1].alias_of=Some(field("ff",false));
 let aliased=validate_architecture(&overlap,&ValidationLimits::default()).unwrap();
 validate_selection(&aliased,&Selection{modes:vec![],features:vec![setting("ff",0),setting("source",0)]}).unwrap();
 println!("GENERIC-BASELINE alias-agree");
 reject(validate_selection(&aliased,&selection),Code::Conflict,"M-ALIAS-CONFLICT");
 reject(validate_selection(&aliased,&selection),Code::Conflict,"N-ALIAS-CONFLICT");
}
#[test]
fn exact_threeway_reserved_three() {
 let mut a=base(); a.templates[0].features=vec![feature("select",0,2)];
 a.templates[0].features[0].domain=ValueDomain::Range{minimum:0,maximum:2};
 for source in ["A","B","C"] {let mut r=a.templates[0].resources[0].clone(); r.name=n(source); a.templates[0].resources.push(r);}
 a.templates[0].connections.push(Connection{name:n("ordered_mux"),sources:["A","B","C"].iter().map(|s|Endpoint{resource:resource(s),pin:n("O"),provenance:p()}).collect(),destination:Endpoint{resource:resource("lut"),pin:n("I"),provenance:p()},selector:Some(field("select",false)),provenance:p()});
 let valid=validate_architecture(&a,&ValidationLimits::default()).unwrap();
 for value in 0..3 {validate_selection(&valid,&Selection{modes:vec![],features:vec![setting("select",value)]}).unwrap();}
 println!("GENERIC-BASELINE threeway-legal");
 reject(validate_selection(&valid,&Selection{modes:vec![],features:vec![setting("select",3)]}),Code::Value,"N-THREEWAY-3");
}
