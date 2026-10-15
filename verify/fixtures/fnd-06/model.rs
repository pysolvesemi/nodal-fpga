//! Fixture-only independent arithmetic model. No production crate or generator imports.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Error { UnsupportedMode, MuxSelection, Width, Missing, Unsupported, Overlap, NonBinary, Package, Address, Alias }
fn lut(init: u16, i: [bool;4]) -> bool {
    let address = usize::from(i[0]) + 2*usize::from(i[1]) + 4*usize::from(i[2]) + 8*usize::from(i[3]);
    (init >> address) & 1 != 0
}
fn next(q:bool,en:bool,sr:bool,d:bool,r:bool,rise:bool)->bool {
    if !rise || !en { q } else if sr {r} else {d}
}
fn mux(inputs:&[bool], select:usize)->Result<bool,Error> { inputs.get(select).copied().ok_or(Error::MuxSelection) }
fn pack(init:u32,ff:u8,carry:u8,reset:u8,source:u8)->Result<u32,Error> {
    if carry!=0 {return Err(Error::UnsupportedMode)}
    if init>65535 || ff>1 || reset>1 {return Err(Error::Width)}
    if source>1 {return Err(Error::MuxSelection)}
    Ok(init | (u32::from(ff)<<16) | (u32::from(reset)<<18) | (u32::from(source)<<19))
}
#[test]
fn exhaustive_lut_independent_bit_table() {
    // Explicit ordered input tuples are independent of the candidate's address helper.
    let inputs = [[false,false,false,false],[true,false,false,false],
    [false,true,false,false],[true,true,false,false],[false,false,true,false],
    [true,false,true,false],[false,true,true,false],[true,true,true,false],
    [false,false,false,true],[true,false,false,true],[false,true,false,true],
    [true,true,false,true],[false,false,true,true],[true,false,true,true],
    [false,true,true,true],[true,true,true,true]];
    let mut count=0u64;
    for init in 0..=u16::MAX {
        // Repeated quotient/remainder builds a table; no candidate address calculation.
        let mut rest=init; let mut table=[false;16];
        for bit in &mut table {*bit=rest%2==1; rest/=2;}
        for (i, expected) in inputs.iter().zip(table) {assert_eq!(lut(init,*i),expected); count+=1;}
    }
    assert_eq!(count,1_048_576); println!("MODEL-LUT-CASES {count}");
}
#[test]
fn asymmetric_literals() {
    let a=[1,1,0,0,1,0,1,1,0,1,1,0,0,1,0,1];
    let b=[0,1,0,0,1,0,0,0,0,0,0,1,0,0,0,0];
    for address in 0..16 {
        let input=[address&1!=0,address&2!=0,address&4!=0,address&8!=0];
        assert_eq!(lut(0xA6D3,input),a[address]==1);
        assert_eq!(lut(0x0812,input),b[address]==1);
    }
}
#[test]
fn exhaustive_register_edges_and_modes() {
    let mut count=0;
    for q in [false,true] {for en in [false,true] {for sr in [false,true] {
    for d in [false,true] {for r in [false,true] {for edge in ["rise","fall","none"] {
        let expected=match(edge,en,sr){("rise",true,true)=>r,("rise",true,false)=>d,_=>q};
        assert_eq!(next(q,en,sr,d,r,edge=="rise"),expected);
        for ff in [false,true] {assert_eq!(if ff {q}else{d},[d,q][usize::from(ff)]);}
        count+=1;
    }}}}}} assert_eq!(count,96); println!("MODEL-REGISTER-CASES {count}");
}
#[test]
fn literal_register_traces() {
    // edge: 1 rising, 0 no edge, -1 falling. Exact accepted witness rows.
    let traces: [&[(i8,bool,bool,bool,bool)];2]=[
      &[(1,true,true,true,false),(0,true,false,true,false),(-1,true,false,true,false),
        (1,false,false,true,false),(1,true,false,true,true),(1,false,true,false,true),
        (0,true,true,true,true),(1,true,true,true,false),(1,true,false,false,false)],
      &[(1,true,true,false,true),(1,false,false,false,true),(1,true,false,false,false),
        (1,false,true,true,false),(1,true,true,false,true)]];
    for (reset, trace) in traces.iter().enumerate() {for initial in [false,true] {
      let mut q=initial; for &(edge,en,sr,d,expected) in *trace {
        q=next(q,en,sr,d,reset==1,edge==1); assert_eq!(q,expected);
      }
    }}
}
#[test]
fn mux_literal_cases_and_reserved_code() {
    for (a,b,s,y) in [(false,false,0,false),(false,false,1,false),(false,true,0,false),
      (false,true,1,true),(true,false,0,true),(true,false,1,false),(true,true,0,true),(true,true,1,true)] {
      assert_eq!(mux(&[a,b],s),Ok(y));
    }
    for s in 0..3 {assert_eq!(mux(&[false,true,false],s),Ok([false,true,false][s]));}
    assert_eq!(mux(&[false,true,false],3),Err(Error::MuxSelection));
}
#[test]
fn literal_config_and_all_bindings() {
    for (ff,r,s,word,frame) in [(0,0,0,0x0A6D3,0x0A6D3000u32),
       (1,0,0,0x1A6D3,0x1A6D3000),(1,1,0,0x5A6D3,0x5A6D3000),(0,0,1,0x8A6D3,0x8A6D3000)] {
      let packed=pack(0xA6D3,ff,0,r,s).unwrap(); assert_eq!(packed,word); assert_eq!(packed<<12,frame);
    }
    let physical=[12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31];
    for (logical,data) in physical.iter().enumerate() {assert_eq!((1u32<<logical)<<12,1u32<<data);}
    assert_eq!(pack(0,0,1,0,0),Err(Error::UnsupportedMode));
    assert_eq!(pack(65536,0,0,0,0),Err(Error::Width));
    assert_eq!(pack(0,0,0,0,2),Err(Error::MuxSelection));
}
// Input-contract cases and graph exact sets are checked independently by behavior.py
// against frozen JSON. The generic production API negatives have separate named tests.

fn validate_fields(fields:&[(&str,&str)], package:&str, frame:u8, bit:u8,
                   owners:&[u8], alias:Option<(bool,bool)>)->Result<u32,Error> {
    use std::collections::BTreeMap;
    if package!="nf-tiny-foundation/1" {return Err(Error::Package)}
    if frame!=0 || !(12..32).contains(&bit) {return Err(Error::Address)}
    for (i,owner) in owners.iter().enumerate() {if owners[..i].contains(owner) {return Err(Error::Overlap)}}
    if let Some((a,b))=alias {if a!=b {return Err(Error::Alias)}}
    let allowed=["init","ff","carry_i0","reset_value","source"];
    let mut values=BTreeMap::new();
    for &(k,v) in fields {
      if !allowed.contains(&k) {return Err(Error::Unsupported)}
      if values.insert(k,v).is_some() {return Err(Error::Overlap)}
      if v.eq_ignore_ascii_case("x") || v.eq_ignore_ascii_case("z") {return Err(Error::NonBinary)}
    }
    if allowed.iter().any(|k|!values.contains_key(k)) {return Err(Error::Missing)}
    let init=u32::from_str_radix(values["init"],16).map_err(|_|Error::Width)?;
    let number=|k|values[k].parse::<u8>().map_err(|_|Error::Width);
    pack(init,number("ff")?,number("carry_i0")?,number("reset_value")?,number("source")?)
}
#[test]
fn named_invalid_input_categories() {
    let base=[("init","A6D3"),("ff","0"),("carry_i0","0"),("reset_value","0"),("source","0")];
    let check=|fields:&[(&str,&str)]|validate_fields(fields,"nf-tiny-foundation/1",0,12,&[0,16,17,18,19],None);
    for (id,index,value,error) in [("N-CARRY",2,"1",Error::UnsupportedMode),
      ("N-SOURCE-RANGE",4,"2",Error::MuxSelection),("N-INIT-WIDTH",0,"10000",Error::Width),
      ("N-SELECT-X",4,"X",Error::NonBinary),("N-SELECT-Z",4,"Z",Error::NonBinary)] {
        let mut f=base; f[index].1=value; assert_eq!(check(&f),Err(error)); println!("MODEL-NEGATIVE {id} {error:?}");
    }
    let mut unknown=base.to_vec(); unknown.push(("async_reset","1"));
    assert_eq!(check(&unknown),Err(Error::Unsupported)); println!("MODEL-NEGATIVE N-UNKNOWN-FEATURE Unsupported");
    let missing=[base[0],base[1],base[2],base[4]];
    assert_eq!(check(&missing),Err(Error::Missing)); println!("MODEL-NEGATIVE N-MISSING-FEATURE Missing");
    assert_eq!(validate_fields(&base,"other",0,12,&[],None),Err(Error::Package)); println!("MODEL-NEGATIVE N-PACKAGE Package");
    for (frame,bit) in [(1,12),(0,0)] {assert_eq!(validate_fields(&base,"nf-tiny-foundation/1",frame,bit,&[],None),Err(Error::Address));}
    println!("MODEL-NEGATIVE N-PADDING-ADDRESS Address");
    assert_eq!(validate_fields(&base,"nf-tiny-foundation/1",0,12,&[16,16],None),Err(Error::Overlap)); println!("MODEL-NEGATIVE N-OVERLAP Overlap");
    assert_eq!(validate_fields(&base,"nf-tiny-foundation/1",0,12,&[],Some((false,true))),Err(Error::Alias)); println!("MODEL-NEGATIVE N-ALIAS-CONFLICT Alias");
    assert_eq!(mux(&[true,false,true],3),Err(Error::MuxSelection)); println!("MODEL-NEGATIVE N-THREEWAY-3 MuxSelection");
}
#[test]
fn independently_enumerated_tiny_reachability() {
    // Complete present-coordinate sets; never read candidate-normalized topology.
    let shapes: [&[(u8,u8)];4]=[&[(0,0)],&[(0,0),(1,0),(0,1),(1,1)],
      &[(0,0),(1,0),(2,0),(0,1),(1,1),(2,1)],
      &[(0,0),(1,0),(1,1),(2,1),(0,2),(2,2)]];
    let links: [&[((u8,u8),(u8,u8))];4]=[&[],&[((0,0),(1,0)),((0,1),(1,1))],
      &[((0,0),(1,0)),((1,0),(2,0)),((0,1),(1,1)),((1,1),(2,1))],
      &[((0,0),(1,0)),((1,1),(2,1))]];
    for (tiles,expected) in shapes.iter().zip(links) {
      let actual:std::collections::BTreeSet<_>=tiles.iter().flat_map(|&(x,y)|
        tiles.iter().filter_map(move |&(a,b)|if a==x+1 && b==y {Some(((x,y),(a,b)))}else{None})).collect();
      assert_eq!(actual,expected.iter().copied().collect());
    }
    println!("MODEL-GRAPH-SHAPES 4");
}
