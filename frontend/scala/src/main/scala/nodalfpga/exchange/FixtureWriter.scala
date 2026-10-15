package nodalfpga.exchange

import com.fasterxml.jackson.core.{JsonEncoding, JsonFactoryBuilder}
import com.fasterxml.jackson.core.io.{CharacterEscapes, SerializedString}
import com.fasterxml.jackson.core.json.JsonWriteFeature
import java.io.ByteArrayOutputStream
import java.nio.charset.StandardCharsets.UTF_8
import java.nio.file.{Files, Path}
import java.security.MessageDigest

/** Small typed authoring witness for exchange 0.1. This is not the production Scala DSL.
  *
  * Checks authoring scalars and keyed collection identities, then delegates JSON token generation
  * to Jackson core. Rust's checked FND-04 adapter remains the architecture semantic authority.
  */
object FixtureWriter:
  val ScalaVersion = "3.3.8"
  val JacksonVersion = "2.21.5"
  val MaxU64: BigInt = (BigInt(1) << 64) - 1

  final case class WriterError(code: String, detail: String)
      extends IllegalArgumentException(s"$code: $detail")

  private def check(ok: Boolean, code: String, detail: String): Unit =
    if !ok then throw WriterError(code, detail)

  def checkedText(value: String, maxBytes: Int = 65536): String =
    var i = 0
    while i < value.length do
      val c = value.charAt(i)
      if Character.isHighSurrogate(c) then
        check(
          i + 1 < value.length && Character.isLowSurrogate(value.charAt(i + 1)),
          "invalid_unicode",
          "unpaired high UTF-16 surrogate"
        )
        i += 2
      else
        check(!Character.isLowSurrogate(c), "invalid_unicode", "unpaired low UTF-16 surrogate")
        i += 1
    check(value.getBytes(UTF_8).length <= maxBytes, "limit", s"text exceeds $maxBytes UTF-8 bytes")
    value

  final case class Name(value: String):
    checkedText(value, 128)
    check(value.nonEmpty, "invalid_name", "name is empty")

  final case class U64(value: BigInt):
    check(value >= 0 && value <= MaxU64, "overflow", "unsigned value is outside u64")
    def json: Json = Json.Text(value.toString)
    def positive: U64 =
      check(value > 0, "invalid_unsigned", "quantity must be positive")
      this
    def width: U64 =
      check(value >= 1 && value <= 64, "overflow", "feature width must be 1..64")
      this
    def partition: U64 =
      check(value <= BigInt("4294967295"), "overflow", "partition must fit u32")
      this

  object U64:
    def decimal(value: String): U64 =
      check(value.matches("0|[1-9][0-9]*"), "invalid_unsigned", "expected minimal ASCII decimal")
      // A huge decimal token is rejected before invoking BigInt's parser.
      check(value.length <= 20, "overflow", "unsigned value is outside u64")
      U64(BigInt(value))

  enum Json:
    case Null
    case Bool(value: Boolean)
    case Integer(value: Int)
    case Text(value: String)
    case Arr(values: Vector[Json])
    case Obj(fields: Vector[(String, Json)])
  import Json.*

  def obj(fields: (String, Json)*): Json = Obj(fields.toVector)
  private def text(value: String): Json = Text(checkedText(value))
  private def names(values: Vector[Name]): Json = Arr(values.map(v => text(v.value)))
  private def nullable[A](value: Option[A])(f: A => Json): Json = value.fold[Json](Null)(f)

  val utf8Ordering: Ordering[String] = new Ordering[String]:
    def compare(left: String, right: String): Int =
      val a = checkedText(left).getBytes(UTF_8)
      val b = checkedText(right).getBytes(UTF_8)
      var i = 0
      while i < a.length && i < b.length do
        val difference = (a(i) & 255) - (b(i) & 255)
        if difference != 0 then return difference
        i += 1
      a.length.compare(b.length)

  private def compareNames(a: Vector[Name], b: Vector[Name]): Int =
    var i = 0
    while i < a.length && i < b.length do
      val result = utf8Ordering.compare(a(i).value, b(i).value)
      if result != 0 then return result
      i += 1
    a.length.compare(b.length)

  private def keyed[A](values: Vector[A], compare: (A, A) => Int)(f: A => Json): Json =
    val sorted = values.sortWith((a, b) => compare(a, b) < 0)
    sorted.sliding(2).foreach { pair =>
      if pair.size == 2 then
        check(compare(pair(0), pair(1)) != 0, "duplicate", "duplicate keyed collection identity")
    }
    Arr(sorted.map(f))

  private def named[A](values: Vector[A])(key: A => Name)(f: A => Json): Json =
    keyed(values, (a: A, b: A) => utf8Ordering.compare(key(a).value, key(b).value))(f)

  private def nameSet(values: Vector[Name]): Json = named(values)(identity)(n => text(n.value))
  private def numberSet(values: Vector[U64]): Json =
    keyed(values, (a: U64, b: U64) => a.value.compare(b.value))(_.json)

  /** Jackson's non-short control escapes must use lowercase hex, with Unicode scalar values
    * literal.
    */
  private object CanonicalEscapes extends CharacterEscapes:
    private val codes = CharacterEscapes.standardAsciiEscapesForJSON()
    (0 until 32).foreach { c =>
      if !Set(8, 9, 10, 12, 13).contains(c) then codes(c) = CharacterEscapes.ESCAPE_CUSTOM
    }
    override def getEscapeCodesForAscii(): Array[Int] = codes
    override def getEscapeSequence(ch: Int): SerializedString =
      if ch < 32 then new SerializedString(f"\\u$ch%04x") else null

  def canonical(value: Json): Array[Byte] =
    // Validate before opening a generator: a late failure cannot expose a partial output file.
    var nodes = 0
    def validate(node: Json, depth: Int): Unit =
      nodes += 1
      check(nodes <= 200000, "limit", "aggregate JSON node ceiling exceeded")
      node match
        case Text(value) => checkedText(value); ()
        case Arr(values) =>
          check(depth < 64, "limit", "container nesting exceeds 64")
          check(values.size <= 16384, "limit", "array entry ceiling exceeded")
          values.foreach(validate(_, depth + 1))
        case Obj(fields) =>
          check(depth < 64, "limit", "container nesting exceeds 64")
          check(fields.size <= 16384, "limit", "object entry ceiling exceeded")
          val seen = scala.collection.mutable.HashSet.empty[String]
          fields.foreach { (key, child) =>
            checkedText(key)
            nodes += 1
            check(nodes <= 200000, "limit", "aggregate JSON node ceiling exceeded")
            check(seen.add(key), "duplicate_key", "duplicate decoded object key")
            validate(child, depth + 1)
          }
        case _ => ()
    validate(value, 0)
    val output = new ByteArrayOutputStream():
      override def write(value: Int): Unit =
        check(count < 8388608, "limit", "canonical document exceeds byte ceiling")
        super.write(value)
      override def write(bytes: Array[Byte], offset: Int, length: Int): Unit =
        check(length <= 8388608 - count, "limit", "canonical document exceeds byte ceiling")
        super.write(bytes, offset, length)
    val factory = new JsonFactoryBuilder()
      .enable(JsonWriteFeature.COMBINE_UNICODE_SURROGATES_IN_UTF8)
      .disable(JsonWriteFeature.WRITE_HEX_UPPER_CASE)
      .build()
    val generator = factory.createGenerator(output, JsonEncoding.UTF8)
    generator.setCharacterEscapes(CanonicalEscapes)
    def emit(node: Json): Unit = node match
      case Null           => generator.writeNull()
      case Bool(value)    => generator.writeBoolean(value)
      case Integer(value) => generator.writeNumber(value)
      case Text(value)    => generator.writeString(value)
      case Arr(values)    =>
        generator.writeStartArray()
        values.foreach(emit)
        generator.writeEndArray()
      case Obj(fields) =>
        generator.writeStartObject()
        fields.sortWith((a, b) => utf8Ordering.compare(a._1, b._1) < 0).foreach { (key, child) =>
          generator.writeFieldName(key)
          emit(child)
        }
        generator.writeEndObject()
    try emit(value)
    finally generator.close()
    val bytes = output.toByteArray
    check(bytes.length <= 8388608, "limit", "canonical document exceeds byte ceiling")
    bytes

  def sha256(bytes: Array[Byte]): String =
    MessageDigest.getInstance("SHA-256").digest(bytes).map(b => f"${b & 255}%02x").mkString

  def digest(value: String): String =
    check(
      value.matches("[0-9a-f]{64}"),
      "invalid_digest",
      "expected 64 lowercase hexadecimal digits"
    )
    value

  private def fingerprint(prefix: String, projection: Array[Byte]): String =
    val hash = MessageDigest.getInstance("SHA-256")
    hash.update(prefix.getBytes(UTF_8))
    hash.update(projection)
    hash.digest().map(b => f"${b & 255}%02x").mkString

  enum ResourceKind(val wire: String):
    case Wire extends ResourceKind("wire")
    case Pip extends ResourceKind("pip")
    case Bel extends ResourceKind("bel")
    case Pin extends ResourceKind("pin")
    case Node extends ResourceKind("node")
    case Site extends ResourceKind("site")
    case Field extends ResourceKind("field")
  enum KeyKind(val wire: String):
    case ResourceType extends KeyKind("resource_type")
    case Template extends KeyKind("template")
    case Domain extends KeyKind("domain")
  enum Direction(val wire: String):
    case Input extends Direction("input")
    case Output extends Direction("output")
  enum DomainKind(val wire: String):
    case Clock extends DomainKind("clock")
    case Power extends DomainKind("power")
    case Configuration extends DomainKind("configuration")
    case Placement extends DomainKind("placement")
    case Routing extends DomainKind("routing")

  final case class Key(kind: KeyKind, namespace: Name, scope: Vector[Name], local: Name):
    check(scope.size <= 64, "limit", "key scope exceeds 64 components")
    check(
      (Vector(namespace, local) ++ scope).map(_.value.getBytes(UTF_8).length).sum <= 4096,
      "limit",
      "portable key exceeds 4096 component bytes"
    )
    def json: Json = obj(
      "kind" -> text(kind.wire),
      "namespace" -> text(namespace.value),
      "scope" -> names(scope),
      "local" -> text(local.value)
    )
    def expect(expected: KeyKind): Key =
      check(kind == expected, "wrong_key_kind", s"expected ${expected.wire}")
      this
  private def compareKeys(a: Key, b: Key): Int =
    val kind = utf8Ordering.compare(a.kind.wire, b.kind.wire)
    if kind != 0 then kind
    else
      val namespace = utf8Ordering.compare(a.namespace.value, b.namespace.value)
      if namespace != 0 then namespace
      else
        val scope = compareNames(a.scope, b.scope)
        if scope != 0 then scope else utf8Ordering.compare(a.local.value, b.local.value)
  private def byKey[A](values: Vector[A])(key: A => Key)(f: A => Json): Json =
    keyed(values, (a: A, b: A) => compareKeys(key(a), key(b)))(f)

  final case class Span(source: String, sourceBytes: U64, start: U64, end: U64):
    checkedText(source, 1024)
    check(start.value <= end.value && end.value <= sourceBytes.value, "range", "invalid byte span")
    def json: Json = obj(
      "source" -> text(source),
      "source_bytes" -> sourceBytes.json,
      "start" -> start.json,
      "end" -> end.json
    )
  final case class Provenance(span: Option[Span] = None, display: Option[String] = None):
    display.foreach(checkedText(_, 1024))
    def json: Json = obj("span" -> nullable(span)(_.json), "display" -> nullable(display)(text))
  val noOrigin: Provenance = Provenance()

  private def record(semantic: Boolean, origin: Provenance)(fields: (String, Json)*): Json =
    Obj(fields.toVector ++ (if semantic then Vector.empty else Vector("provenance" -> origin.json)))

  final case class Pin(name: Name, direction: Direction, width: U64, origin: Provenance = noOrigin):
    width.positive
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "direction" -> text(direction.wire),
      "width" -> width.json
    )
  final case class ResourceType(
      key: Key,
      kind: ResourceKind,
      pins: Vector[Pin],
      modes: Vector[Name],
      origin: Provenance = noOrigin
  ):
    key.expect(KeyKind.ResourceType)
    def json(s: Boolean): Json = record(s, origin)(
      "key" -> key.json,
      "kind" -> text(kind.wire),
      "pins" -> Arr(pins.map(_.json(s))),
      "modes" -> nameSet(modes)
    )
  final case class Domain(key: Key, kind: DomainKind, origin: Provenance = noOrigin):
    key.expect(KeyKind.Domain)
    def json(s: Boolean): Json = record(s, origin)("key" -> key.json, "kind" -> text(kind.wire))
  private def domains(values: Vector[Domain], s: Boolean): Json =
    keyed(
      values,
      (a: Domain, b: Domain) => {
        val key = compareKeys(a.key, b.key)
        if key != 0 then key else utf8Ordering.compare(a.kind.wire, b.kind.wire)
      }
    )(_.json(s))
  final case class ResourceRef(
      path: Vector[Name],
      name: Name,
      kind: ResourceKind,
      origin: Provenance = noOrigin
  ):
    check(path.size <= 64, "limit", "reference path exceeds 64 components")
    def json(s: Boolean): Json = record(s, origin)(
      "path" -> names(path),
      "name" -> text(name.value),
      "kind" -> text(kind.wire)
    )
  private def compareRefs(a: ResourceRef, b: ResourceRef): Int =
    val kind = utf8Ordering.compare(a.kind.wire, b.kind.wire)
    if kind != 0 then kind
    else
      val path = compareNames(a.path, b.path)
      if path != 0 then path else utf8Ordering.compare(a.name.value, b.name.value)
  final case class FieldRef(path: Vector[Name], name: Name, origin: Provenance = noOrigin):
    check(path.size <= 64, "limit", "field path exceeds 64 components")
    def json(s: Boolean): Json =
      record(s, origin)("path" -> names(path), "name" -> text(name.value))
  final case class Endpoint(resource: ResourceRef, pin: Name, origin: Provenance = noOrigin):
    def json(s: Boolean): Json =
      record(s, origin)("resource" -> resource.json(s), "pin" -> text(pin.value))
  final case class Resource(
      name: Name,
      kind: ResourceKind,
      resourceType: Key,
      aliasOf: Option[ResourceRef] = None,
      memberships: Vector[Domain] = Vector.empty,
      origin: Provenance = noOrigin
  ):
    resourceType.expect(KeyKind.ResourceType)
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "kind" -> text(kind.wire),
      "resource_type" -> resourceType.json,
      "alias_of" -> nullable(aliasOf)(_.json(s)),
      "domains" -> domains(memberships, s)
    )
  final case class Instance(
      name: Name,
      template: Key,
      partition: Option[U64],
      memberships: Vector[Domain] = Vector.empty,
      origin: Provenance = noOrigin
  ):
    template.expect(KeyKind.Template)
    partition.foreach(_.partition)
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "template" -> template.json,
      "partition" -> nullable(partition)(_.json),
      "domains" -> domains(memberships, s)
    )
  final case class Connection(
      name: Name,
      sources: Vector[Endpoint],
      destination: Endpoint,
      selector: Option[FieldRef] = None,
      origin: Provenance = noOrigin
  ):
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "sources" -> Arr(sources.map(_.json(s))),
      "destination" -> destination.json(s),
      "selector" -> nullable(selector)(_.json(s))
    )
  final case class ModeGroup(
      name: Name,
      resources: Vector[ResourceRef],
      modes: Vector[Name],
      origin: Provenance = noOrigin
  ):
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "resources" -> keyed(resources, compareRefs)(_.json(s)),
      "modes" -> nameSet(modes)
    )
  final case class ModeChoice(group: Name, mode: Name, origin: Provenance = noOrigin):
    def json(s: Boolean): Json =
      record(s, origin)("group" -> text(group.value), "mode" -> text(mode.value))
  final case class Storage(
      name: Name,
      owner: ResourceRef,
      bits: U64,
      origin: Provenance = noOrigin
  ):
    bits.positive
    def json(s: Boolean): Json =
      record(s, origin)("name" -> text(name.value), "owner" -> owner.json(s), "bits" -> bits.json)
  final case class BitRange(start: U64, length: U64):
    check(start.value + length.value <= MaxU64, "overflow", "bit range end exceeds u64")
    def json: Json = obj("unit" -> text("bit"), "start" -> start.json, "length" -> length.json)
  enum ValueDomain:
    case Any
    case Range(minimum: U64, maximum: U64)
    case Set(values: Vector[U64])
    def json: Json = this match
      case Any                     => obj("kind" -> text("any"))
      case Range(minimum, maximum) =>
        check(minimum.value <= maximum.value, "range", "inverted value range")
        obj("kind" -> text("range"), "minimum" -> minimum.json, "maximum" -> maximum.json)
      case Set(values) => obj("kind" -> text("set"), "values" -> numberSet(values))
  final case class Feature(
      name: Name,
      owner: ResourceRef,
      storage: Name,
      range: BitRange,
      width: U64,
      domain: ValueDomain,
      guard: Vector[ModeChoice] = Vector.empty,
      aliasOf: Option[FieldRef] = None,
      origin: Provenance = noOrigin
  ):
    width.width
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "owner" -> owner.json(s),
      "storage" -> text(storage.value),
      "range" -> range.json,
      "width" -> width.json,
      "domain" -> domain.json,
      "guard" -> named(guard)(_.group)(_.json(s)),
      "alias_of" -> nullable(aliasOf)(_.json(s))
    )
  final case class Template(
      key: Key,
      resources: Vector[Resource] = Vector.empty,
      children: Vector[Instance] = Vector.empty,
      modeGroups: Vector[ModeGroup] = Vector.empty,
      storage: Vector[Storage] = Vector.empty,
      features: Vector[Feature] = Vector.empty,
      connections: Vector[Connection] = Vector.empty,
      origin: Provenance = noOrigin
  ):
    key.expect(KeyKind.Template)
    def json(s: Boolean): Json = record(s, origin)(
      "key" -> key.json,
      "resources" -> named(resources)(_.name)(_.json(s)),
      "children" -> named(children)(_.name)(_.json(s)),
      "mode_groups" -> named(modeGroups)(_.name)(_.json(s)),
      "storage" -> named(storage)(_.name)(_.json(s)),
      "features" -> named(features)(_.name)(_.json(s)),
      "connections" -> named(connections)(_.name)(_.json(s))
    )

  final case class Capability(id: String, revision: Int):
    checkedText(id, 128)
    check(
      id.matches("[a-z][a-z0-9.-]*/[a-z][a-z0-9._-]*"),
      "invalid_capability",
      "bad capability ID"
    )
    check(revision >= 0 && revision <= 65535, "overflow", "capability revision must fit u16")
    def json: Json = obj("id" -> text(id), "revision" -> Integer(revision))
  final case class Annotations(entries: Vector[(Capability, Json)] = Vector.empty):
    private val ids = entries.map(_._1.id)
    check(ids.distinct.size == ids.size, "duplicate", "duplicate annotation capability")
    def data: Json = Obj(entries.map((capability, value) => capability.id -> value))
    def capabilities: Json =
      keyed(entries.map(_._1), (a: Capability, b: Capability) => utf8Ordering.compare(a.id, b.id))(
        _.json
      )

  private def envelope(
      format: String,
      profile: String,
      feature: String,
      body: Json,
      annotations: Annotations,
      semantic: Boolean
  ): Json =
    val fields = Vector(
      "format" -> text(format),
      "version" -> obj("major" -> Integer(0), "minor" -> Integer(1)),
      "profile" -> obj("id" -> text(profile), "revision" -> Integer(1)),
      "required_features" -> Arr(Vector(Capability(feature, 1).json)),
      "body" -> body
    )
    Obj(fields ++ (if semantic then Vector.empty
                   else
                     Vector(
                       "annotations" -> annotations.data,
                       "optional_features" -> annotations.capabilities
                     )))

  trait Document:
    def format: String
    def profile: String
    def capability: String
    def prefix: String
    def annotations: Annotations
    def body(semantic: Boolean): Json
    final def projection: Array[Byte] = canonical(
      envelope(format, profile, capability, body(true), annotations, true)
    )
    final def identity: String = fingerprint(prefix, projection)
    final def bytes: Array[Byte] = canonical(
      envelope(format, profile, capability, body(false), annotations, false)
    )

  final case class Architecture(
      namespace: Name,
      resourceTypes: Vector[ResourceType],
      templates: Vector[Template],
      roots: Vector[Instance],
      partitions: Vector[U64],
      domainDefinitions: Vector[Domain] = Vector.empty,
      connections: Vector[Connection] = Vector.empty,
      origin: Provenance = noOrigin,
      annotations: Annotations = Annotations()
  ) extends Document:
    val format = "nodal-fpga.arch"
    val profile = "structural-selection"
    val capability = "nodal-fpga/arch.structural-selection"
    val prefix = "nodal-fpga.arch.semantic.v1\n"
    partitions.foreach(_.partition)
    check(
      roots.forall(_.partition.nonEmpty),
      "missing_partition",
      "each root needs an explicit partition"
    )
    def body(s: Boolean): Json =
      val fields = Vector(
        "namespace" -> text(namespace.value),
        "resource_types" -> byKey(resourceTypes)(_.key)(_.json(s)),
        "templates" -> byKey(templates)(_.key)(_.json(s)),
        "roots" -> named(roots)(_.name)(_.json(s)),
        "partitions" -> numberSet(partitions),
        "domains" -> byKey(domainDefinitions)(_.key)(_.json(s)),
        "connections" -> named(connections)(_.name)(_.json(s))
      )
      record(s, origin)(
        (fields ++ (if s then Vector.empty else Vector("semantic_id" -> text(identity))))*
      )

  final case class Artifact(sha256: String, bytes: U64):
    digest(sha256)
    def json: Json = obj("sha256" -> text(sha256), "bytes" -> bytes.json)
  final case class ToolOption(name: Name, value: String):
    checkedText(value, 1024)
    def json: Json = obj("name" -> text(name.value), "value" -> text(value))
  enum UnboundReason(val wire: String):
    case NotSupplied extends UnboundReason("not-supplied")
    case FoundationUnimplemented extends UnboundReason("foundation-unimplemented")
  private def shortText(value: String): Json =
    check(value.nonEmpty, "invalid_name", "binding text must be nonempty")
    Text(checkedText(value, 128))
  enum ToolBinding:
    case Unbound(reason: UnboundReason)
    case Bound(
        id: String,
        version: String,
        implementationSha256: String,
        options: Vector[ToolOption]
    )
    def json: Json = this match
      case Unbound(reason) => obj("state" -> text("unbound"), "reason" -> text(reason.wire))
      case Bound(id, version, hash, options) =>
        obj(
          "state" -> text("bound"),
          "id" -> shortText(id),
          "version" -> shortText(version),
          "implementation_sha256" -> text(digest(hash)),
          "options" -> named(options)(_.name)(_.json)
        )
  enum ViewBinding:
    case Unbound(reason: UnboundReason)
    case Bound(revision: String, artifact: Artifact)
    def json: Json = this match
      case Unbound(reason) => obj("state" -> text("unbound"), "reason" -> text(reason.wire))
      case Bound(revision, artifact) =>
        obj(
          "state" -> text("bound"),
          "revision" -> shortText(revision),
          "artifact" -> artifact.json
        )
  final case class Library(id: String, revision: String, artifact: Artifact):
    def json: Json =
      obj("id" -> shortText(id), "revision" -> shortText(revision), "artifact" -> artifact.json)
  final case class Package(
      architectureId: String,
      architecture: Artifact,
      authoring: ToolBinding,
      libraries: Vector[Library] = Vector.empty,
      compiler: ToolBinding = ToolBinding.Unbound(UnboundReason.FoundationUnimplemented),
      backend: ToolBinding = ToolBinding.Unbound(UnboundReason.FoundationUnimplemented),
      views: Map[String, ViewBinding] = Map.empty,
      macroBindings: Option[ViewBinding] = None,
      annotations: Annotations = Annotations()
  ) extends Document:
    val format = "nodal-fpga.package-manifest"
    val profile = "software-package"
    val capability = "nodal-fpga/package.software-inspection"
    val prefix = "nodal-fpga.package.build.v1\n"
    val roles = Vector(
      "device_db",
      "physical_implementation",
      "technology",
      "configuration_map",
      "transport",
      "activation",
      "timing_datasets",
      "external_pin_map"
    )
    check(views.keys.forall(roles.contains), "unknown_field", "unrecognized package view role")
    def body(s: Boolean): Json =
      val fields = Vector(
        "architecture" -> obj(
          "semantic_id" -> text(digest(architectureId)),
          "artifact" -> architecture.json
        ),
        "libraries" -> keyed(
          libraries,
          (a: Library, b: Library) => utf8Ordering.compare(a.id, b.id)
        )(_.json),
        "authoring" -> authoring.json,
        "compiler" -> compiler.json,
        "backend" -> backend.json,
        "macro_bindings" -> macroBindings.fold(
          obj("state" -> text("absent"), "reason" -> text("no-hard-macros"))
        )(_.json)
      ) ++
        roles.map(role =>
          role -> views
            .getOrElse(role, ViewBinding.Unbound(UnboundReason.FoundationUnimplemented))
            .json
        )
      Obj(fields ++ (if s then Vector.empty else Vector("build_id" -> text(identity))))

  final case class Cell(name: Name, resourceType: Key, mode: Name, origin: Provenance = noOrigin):
    resourceType.expect(KeyKind.ResourceType)
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "resource_type" -> resourceType.json,
      "mode" -> text(mode.value)
    )
  final case class Port(
      name: Name,
      direction: Direction,
      width: U64,
      origin: Provenance = noOrigin
  ):
    width.positive
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "direction" -> text(direction.wire),
      "width" -> width.json
    )
  enum DesignEndpoint:
    case CellPin(cell: Name, pin: Name, bit: U64, origin: Provenance = noOrigin)
    case PortBit(port: Name, bit: U64, origin: Provenance = noOrigin)
    case Constant(value: Boolean, origin: Provenance = noOrigin)
    def json(s: Boolean): Json = this match
      case CellPin(cell, pin, bit, origin) =>
        record(s, origin)(
          "kind" -> text("cell"),
          "cell" -> text(cell.value),
          "pin" -> text(pin.value),
          "bit" -> bit.json
        )
      case PortBit(port, bit, origin) =>
        record(s, origin)("kind" -> text("port"), "port" -> text(port.value), "bit" -> bit.json)
      case Constant(value, origin) =>
        record(s, origin)("kind" -> text("constant"), "value" -> text(if value then "1" else "0"))
  private def compareLoads(a: DesignEndpoint, b: DesignEndpoint): Int =
    import DesignEndpoint.*
    def tuple(value: DesignEndpoint): (String, String, String, BigInt) = value match
      case CellPin(cell, pin, bit, _) => ("cell", cell.value, pin.value, bit.value)
      case PortBit(port, bit, _)      => ("port", port.value, "", bit.value)
      case Constant(_, _) => throw WriterError("invalid_endpoint", "constant cannot be a load")
    val aa = tuple(a)
    val bb = tuple(b)
    val comparisons = Vector(
      utf8Ordering.compare(aa._1, bb._1),
      utf8Ordering.compare(aa._2, bb._2),
      utf8Ordering.compare(aa._3, bb._3),
      aa._4.compare(bb._4)
    )
    comparisons.find(_ != 0).getOrElse(0)
  final case class Net(
      name: Name,
      driver: DesignEndpoint,
      loads: Vector[DesignEndpoint],
      origin: Provenance = noOrigin
  ):
    check(loads.nonEmpty, "invalid_endpoint", "net requires at least one load")
    check(
      !loads.exists(_.isInstanceOf[DesignEndpoint.Constant]),
      "invalid_endpoint",
      "constant cannot be a load"
    )
    def json(s: Boolean): Json = record(s, origin)(
      "name" -> text(name.value),
      "driver" -> driver.json(s),
      "loads" -> keyed(loads, compareLoads)(_.json(s))
    )
  final case class Design(
      namespace: Name,
      name: Name,
      targetBuildId: String,
      cells: Vector[Cell],
      ports: Vector[Port],
      nets: Vector[Net],
      origin: Provenance = noOrigin,
      annotations: Annotations = Annotations()
  ) extends Document:
    val format = "nodal-fpga.mapped-design"
    val profile = "mapped-structural"
    val capability = "nodal-fpga/design.structural"
    val prefix = "nodal-fpga.design.semantic.v1\n"
    def body(s: Boolean): Json =
      val fields = Vector(
        "namespace" -> text(namespace.value),
        "name" -> text(name.value),
        "target_build_id" -> text(digest(targetBuildId)),
        "cells" -> named(cells)(_.name)(_.json(s)),
        "ports" -> named(ports)(_.name)(_.json(s)),
        "nets" -> named(nets)(_.name)(_.json(s))
      )
      record(s, origin)(
        (fields ++ (if s then Vector.empty else Vector("semantic_id" -> text(identity))))*
      )

  // Hand-stated primary semantics from the independently authored EXPECTED.md, not imported JSON.
  // Deliberately permute keyed sets; the ordered pin and mux vectors remain untouched.
  def exampleArchitecture: Architecture =
    val namespace = Name("golden")
    def key(kind: KeyKind, local: String): Key = Key(kind, namespace, Vector.empty, Name(local))
    val primitive = key(KeyKind.ResourceType, "generic-cell")
    val tileKey = key(KeyKind.Template, "tile")
    def ref(name: String, path: String*): ResourceRef =
      ResourceRef(path.toVector.map(Name.apply), Name(name), ResourceKind.Bel)
    def endpoint(name: String, pin: String, path: String*): Endpoint =
      Endpoint(ref(name, path*), Name(pin))
    val domainDefinitions = Vector(
      Domain(key(KeyKind.Domain, "power1"), DomainKind.Power),
      Domain(key(KeyKind.Domain, "clock"), DomainKind.Clock),
      Domain(key(KeyKind.Domain, "power0"), DomainKind.Power),
      Domain(key(KeyKind.Domain, "config"), DomainKind.Configuration)
    )
    val tile = Template(
      tileKey,
      resources = Vector("west", "sink", "east", "local").map(n =>
        Resource(Name(n), ResourceKind.Bel, primitive)
      ),
      modeGroups = Vector(
        ModeGroup(Name("operation"), Vector(ref("sink")), Vector(Name("normal"), Name("alternate")))
      ),
      storage = Vector(Storage(Name("cfg"), ref("sink"), U64(2))),
      features = Vector(
        Feature(
          Name("route"),
          ref("sink"),
          Name("cfg"),
          BitRange(U64(0), U64(2)),
          U64(2),
          ValueDomain.Set(Vector(U64(2), U64(0), U64(1))),
          origin = Provenance(None, Some("Scala fixture mux selector"))
        )
      ),
      connections = Vector(
        Connection(
          Name("mux"),
          Vector(endpoint("east", "O"), endpoint("local", "O"), endpoint("west", "O")),
          endpoint("sink", "I"),
          Some(FieldRef(Vector.empty, Name("route")))
        )
      )
    )
    Architecture(
      namespace,
      Vector(
        ResourceType(
          primitive,
          ResourceKind.Bel,
          Vector(Pin(Name("I"), Direction.Input, U64(1)), Pin(Name("O"), Direction.Output, U64(1))),
          Vector(Name("normal"), Name("alternate"))
        )
      ),
      Vector(tile),
      Vector("t2", "t0", "t1").map { root =>
        val power = if root == "t0" then "power0" else "power1"
        Instance(
          Name(root),
          tileKey,
          Some(U64(0)),
          domainDefinitions.filter(d => Set("clock", "config", power).contains(d.key.local.value))
        )
      },
      Vector(U64(0)),
      domainDefinitions,
      Vector(
        Connection(Name("edge1"), Vector(endpoint("sink", "O", "t1")), endpoint("west", "I", "t2")),
        Connection(Name("edge0"), Vector(endpoint("sink", "O", "t0")), endpoint("west", "I", "t1"))
      ),
      origin = Provenance(None, Some("Three independent mux tiles emitted by Scala")),
      annotations = Annotations(
        Vector(
          Capability("scala.example/review", 1) -> obj(
            "provenance" -> text("annotation payload is preserved"),
            "unicode" -> obj("\uD800\uDC00" -> text("supplementary"), "\uE000" -> text("BMP")),
            "semantic_id" -> text("ordinary nonsemantic annotation data")
          )
        )
      )
    )

  def examplePackage(architecture: Architecture, sourceHash: String): Package =
    val bytes = architecture.bytes
    Package(
      architecture.identity,
      Artifact(sha256(bytes), U64(BigInt(bytes.length))),
      ToolBinding.Bound(
        "nodal-fpga/scala-fixture-writer",
        "0.1",
        digest(sourceHash),
        Vector(
          ToolOption(Name("scala_compiler"), "org.scala-lang:scala3-compiler_3"),
          ToolOption(Name("scala_version"), ScalaVersion),
          ToolOption(Name("json_generator"), "com.fasterxml.jackson.core:jackson-core"),
          ToolOption(Name("json_generator_version"), JacksonVersion),
          ToolOption(
            Name("scalac_options"),
            "-deprecation -feature -unchecked -Werror -Wunused:all"
          )
        )
      )
    )

  def exampleDesign(targetBuildId: String): Design =
    import DesignEndpoint.*
    val primitive = Key(KeyKind.ResourceType, Name("golden"), Vector.empty, Name("generic-cell"))
    def cell(name: String, pin: String): DesignEndpoint = CellPin(Name(name), Name(pin), U64(0))
    def port(name: String, bit: Int): DesignEndpoint = PortBit(Name(name), U64(BigInt(bit)))
    Design(
      Name("golden-design"),
      Name("demo"),
      targetBuildId,
      Vector(
        Cell(Name("c1"), primitive, Name("alternate")),
        Cell(Name("c0"), primitive, Name("normal"))
      ),
      Vector(
        Port(Name("out"), Direction.Output, U64(2)),
        Port(Name("in"), Direction.Input, U64(2)),
        Port(Name("flag"), Direction.Output, U64(1))
      ),
      Vector(
        Net(Name("n3"), Constant(true), Vector(port("flag", 0))),
        Net(Name("n1"), cell("c0", "O"), Vector(port("out", 0), cell("c1", "I"))),
        Net(Name("n0"), port("in", 0), Vector(cell("c0", "I"))),
        Net(Name("n2"), cell("c1", "O"), Vector(port("out", 1)))
      )
    )

  def main(args: Array[String]): Unit =
    check(args.length == 2, "usage", "FixtureWriter <output-directory> <verified-source-sha256>")
    val sourceHash = digest(args(1))
    val architecture = exampleArchitecture
    val pkg = examplePackage(architecture, sourceHash)
    val design = exampleDesign(pkg.identity)
    val documents = Vector("architecture" -> architecture, "package" -> pkg, "design" -> design)
    // Construct all output bytes before touching the output directory.
    val files = documents.flatMap { (name, document) =>
      Vector(s"$name.json" -> document.bytes, s"$name.projection.json" -> document.projection)
    }
    val identities = Vector("authoring_source_sha256=" + sourceHash) ++ documents.map {
      (name, document) =>
        s"$name.identity=${document.identity}"
    } ++ files.map { (name, bytes) => s"$name.bytes=${bytes.length} sha256=${sha256(bytes)}" }
    val output = Path.of(args(0))
    Files.createDirectories(output)
    files.foreach { (name, bytes) => Files.write(output.resolve(name), bytes); () }
    Files.writeString(output.resolve("identities.txt"), identities.mkString("", "\n", "\n"), UTF_8)
    identities.foreach(println)
    println("This increment does not affect generated Verilog.")
