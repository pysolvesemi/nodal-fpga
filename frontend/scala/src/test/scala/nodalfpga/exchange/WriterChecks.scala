package nodalfpga.exchange

import java.nio.charset.StandardCharsets.UTF_8
import java.nio.file.{Files, Path}
import nodalfpga.exchange.FixtureWriter.*
import nodalfpga.exchange.FixtureWriter.Json.*

/** Executable checks with no test-framework dependency and no JSON reader on the Scala side. */
object WriterChecks:
  private var passed = 0
  private def test(name: String)(run: => Unit): Unit =
    run
    passed += 1
    println(s"PASS $name")
  private def rejects(code: String)(run: => Any): Unit =
    try
      run
      throw new AssertionError(s"expected $code rejection")
    catch case error: WriterError => assert(error.code == code, s"expected $code, observed $error")
  private def string(value: Json): String = new String(canonical(value), UTF_8)
  private def equalBytes(actual: Array[Byte], expected: Array[Byte]): Unit =
    assert(java.util.Arrays.equals(actual, expected), "byte mismatch")

  def main(args: Array[String]): Unit =
    require(args.length <= 1, "WriterChecks [independent-full-goldens-directory]")
    test("exact BigInt unsigned quantities across machine-number boundaries") {
      Vector(
        "0",
        "4294967295",
        "9007199254740991",
        "9007199254740992",
        "9007199254740993",
        "9223372036854775808",
        "18446744073709551615"
      ).foreach { value =>
        assert(string(U64.decimal(value).json) == s"\"$value\"")
      }
      rejects("overflow")(U64.decimal("18446744073709551616"))
      rejects("overflow")(U64(-1))
      rejects("overflow")(U64.decimal("9" * 100000))
    }
    test("reject noncanonical decoded unsigned grammar") {
      Vector("", "+1", "01", "-1", "-0", " 1", "1 ", "1.0", "1e0", "١", "１２").foreach { value =>
        rejects("invalid_unsigned")(U64.decimal(value))
      }
    }
    test("narrow unsigned fields, bit ranges and source byte spans") {
      U64.decimal("4294967295").partition
      rejects("overflow")(U64.decimal("4294967296").partition)
      U64(64).width
      rejects("overflow")(U64(0).width)
      rejects("overflow")(U64(65).width)
      rejects("invalid_unsigned")(U64(0).positive)
      BitRange(U64(MaxU64 - 1), U64(1))
      rejects("overflow")(BitRange(U64(MaxU64), U64(1)))
      Span("source", U64(MaxU64), U64(MaxU64 - 1), U64(MaxU64))
      rejects("range")(Span("source", U64(3), U64(2), U64(4)))
      rejects("range")(Span("source", U64(3), U64(2), U64(1)))
    }
    test("strict UTF-16 and exact UTF-8 name/provenance bounds") {
      Name("é" * 64)
      rejects("limit")(Name("é" * 65))
      rejects("invalid_name")(Name(""))
      Vector("\uD800", "\uDC00", "a\uD800b", "\uD800\uD800", "\uDC00\uD800").foreach { value =>
        rejects("invalid_unicode")(checkedText(value))
        rejects("invalid_unicode")(canonical(Text(value)))
      }
      checkedText("\uD800\uDC00\uDBFF\uDFFF")
      Provenance(None, Some("é" * 512))
      rejects("limit")(Provenance(None, Some("é" * 513)))
      Span("é" * 512, U64(0), U64(0), U64(0))
      rejects("limit")(Span("é" * 513, U64(0), U64(0), U64(0)))
    }
    test("unsigned UTF-8 object order and literal supplementary scalars") {
      val result = string(obj("\uD800\uDC00" -> Text("supplementary"), "\uE000" -> Text("BMP")))
      assert(result == "{\"\uE000\":\"BMP\",\"\uD800\uDC00\":\"supplementary\"}", result)
      assert(utf8Ordering.compare("\uE000", "\uD800\uDC00") < 0)
      assert(utf8Ordering.compare("é", "z") > 0)
      assert(utf8Ordering.compare("a", "aa") < 0)
      assert(string(Text("/é\uFEFF\uD800\uDC00")) == "\"/é\uFEFF\uD800\uDC00\"")
    }
    test("canonical escapes and exact minimal integers") {
      assert(
        string(Text("\"\\\b\f\n\r\t\u0000\u000b\u001f/")) ==
          "\"\\\"\\\\\\b\\f\\n\\r\\t\\u0000\\u000b\\u001f/\""
      )
      assert(
        string(Arr(Vector(Integer(Int.MinValue), Integer(0), Integer(Int.MaxValue)))) ==
          "[-2147483648,0,2147483647]"
      )
      equalBytes(canonical(obj()), "{}".getBytes(UTF_8))
      rejects("duplicate_key")(canonical(obj("a" -> Null, "a" -> Bool(true))))
    }
    test("container depth, decoded text and immediate collection ceilings") {
      def nested(depth: Int, mode: Int): Json = (0 until depth).foldLeft[Json](Null) {
        (value, index) =>
          if mode == 0 || (mode == 2 && index % 2 == 0) then Arr(Vector(value))
          else obj("x" -> value)
      }
      (0 to 2).foreach { mode =>
        canonical(nested(64, mode))
        rejects("limit")(canonical(nested(65, mode)))
      }
      canonical(Text("a" * 65536))
      rejects("limit")(canonical(Text("a" * 65537)))
      canonical(Arr(Vector.fill(16384)(Null)))
      rejects("limit")(canonical(Arr(Vector.fill(16385)(Null))))
      canonical(Arr(Vector.fill(12)(Arr(Vector.fill(16384)(Null)))))
      rejects("limit")(canonical(Arr(Vector.fill(13)(Arr(Vector.fill(16384)(Null))))))
      rejects("limit")(canonical(Arr(Vector.fill(129)(Text("a" * 65536)))))
    }
    test("portable key tuple and raw name handling") {
      val namespace = Name("ns")
      Key(KeyKind.Template, namespace, Vector(Name("a/b"), Name("..")), Name("x"))
      Key(KeyKind.Template, namespace, Vector.fill(31)(Name("a" * 128)), Name("x" * 126))
      rejects("limit")(
        Key(KeyKind.Template, Name("nnn"), Vector.fill(31)(Name("a" * 128)), Name("x" * 126))
      )
      rejects("limit")(Key(KeyKind.Template, namespace, Vector.fill(65)(Name("x")), Name("x")))
      rejects("wrong_key_kind")(
        Key(KeyKind.Domain, namespace, Vector.empty, Name("x")).expect(KeyKind.Template)
      )
    }
    test("standard SHA-256 vector") {
      assert(
        sha256(
          "abc".getBytes(UTF_8)
        ) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
      )
      rejects("invalid_digest")(digest("A" * 64))
      rejects("invalid_digest")(digest("a" * 63))
    }
    val architecture = exampleArchitecture
    test("architecture agrees with independent semantic hash and retains hierarchy") {
      assert(
        architecture.identity == "0c5e51acf90f91981b7e3375e5ab58b05d20020aa51a594008f8d7a30e1c80a4"
      )
      assert(architecture.templates.size == 1 && architecture.roots.size == 3)
      assert(
        architecture.templates.head.connections.head.sources
          .map(_.resource.name.value) == Vector("east", "local", "west")
      )
      assert(architecture.connections.size == 2)
    }
    test("set permutations preserve canonical full bytes") {
      equalBytes(
        architecture.bytes,
        architecture
          .copy(
            roots = architecture.roots.reverse,
            resourceTypes = architecture.resourceTypes.map(t => t.copy(modes = t.modes.reverse)),
            domainDefinitions = architecture.domainDefinitions.reverse,
            connections = architecture.connections.reverse
          )
          .bytes
      )
      val tile = architecture.templates.head
      val feature = tile.features.head
      equalBytes(
        architecture.bytes,
        architecture
          .copy(templates =
            Vector(
              tile.copy(
                resources = tile.resources.reverse,
                features =
                  Vector(feature.copy(domain = ValueDomain.Set(Vector(U64(1), U64(2), U64(0)))))
              )
            )
          )
          .bytes
      )
    }
    test("ordered pin/mux vectors match independent changed IDs") {
      assert(
        architecture
          .copy(resourceTypes = architecture.resourceTypes.map(t => t.copy(pins = t.pins.reverse)))
          .identity ==
          "de3baecf45cb9e1354f050b8861728e2f2743087aed639b94a785eae3ab0004a"
      )
      assert(
        architecture
          .copy(templates =
            architecture.templates.map(t =>
              t.copy(connections = t.connections.map(c => c.copy(sources = c.sources.reverse)))
            )
          )
          .identity ==
          "817e6d3b7b950ccbf30a1b03886eb823135bfc328f6086e61f80599d3b252f8a"
      )
    }
    test("duplicate sets are rejected before a dump") {
      rejects("duplicate")(
        architecture.copy(roots = architecture.roots :+ architecture.roots.head).bytes
      )
      rejects("duplicate")(architecture.copy(partitions = Vector(U64(0), U64(0))).bytes)
      rejects("duplicate")(
        architecture
          .copy(resourceTypes =
            architecture.resourceTypes
              .map(t => t.copy(modes = Vector(Name("normal"), Name("normal"))))
          )
          .bytes
      )
      rejects("duplicate")(
        Annotations(Vector(Capability("a/b", 1) -> Null, Capability("a/b", 2) -> Null))
      )
      rejects("missing_partition")(
        architecture.copy(roots = architecture.roots.map(_.copy(partition = None)))
      )
    }
    test("schema-directed cold fields preserve identity and change raw artifact") {
      val changed = architecture.copy(
        origin = Provenance(None, Some("changed")),
        annotations = Annotations(
          Vector(
            Capability("a/b", 1) -> obj(
              "semantic_id" -> Text("other"),
              "provenance" -> obj("anything" -> Text("retained"))
            )
          )
        )
      )
      equalBytes(architecture.projection, changed.projection)
      assert(sha256(architecture.bytes) != sha256(changed.bytes))
      assert(new String(changed.bytes, UTF_8).contains("\"anything\":\"retained\""))
      val renamed = architecture.copy(namespace = Name("different"))
      assert(architecture.identity != renamed.identity)
    }
    val sourceHash = "1" * 64
    val pkg = examplePackage(architecture, sourceHash)
    test("actual Scala tool identity, raw artifact binding and explicit unbound views") {
      assert(new String(pkg.bytes, UTF_8).contains("nodal-fpga/scala-fixture-writer"))
      assert(pkg.architecture.bytes.value == BigInt(architecture.bytes.length))
      assert(pkg.architecture.sha256 == sha256(architecture.bytes))
      assert(examplePackage(architecture, "2" * 64).identity != pkg.identity)
      assert(
        pkg
          .copy(views =
            Map("configuration_map" -> ViewBinding.Bound("1", Artifact("3" * 64, U64(1))))
          )
          .identity != pkg.identity
      )
      rejects("unknown_field")(
        pkg.copy(views = Map("design" -> ViewBinding.Unbound(UnboundReason.NotSupplied)))
      )
      val options = Vector(ToolOption(Name("x"), "1"), ToolOption(Name("x"), "2"))
      rejects("duplicate")(
        pkg.copy(authoring = ToolBinding.Bound("a", "1", sourceHash, options)).bytes
      )
    }
    test("mapped-design independent hash, load order and exact target binding") {
      val handTarget = "0cbc4eb05c0f661740158587135aa55b4e03ab74f6a9e5e1dcfa95e3c42fbf9f"
      val handDesign = exampleDesign(handTarget)
      assert(
        handDesign.identity == "bae95cd16fc8ffa058248eb3b83ea91bd6963b62833c48f04abb7d961265cddd"
      )
      equalBytes(
        handDesign.bytes,
        handDesign
          .copy(nets = handDesign.nets.reverse.map(n => n.copy(loads = n.loads.reverse)))
          .bytes
      )
      assert(handDesign.identity != exampleDesign(pkg.identity).identity)
      rejects("invalid_endpoint")(
        Net(Name("bad"), DesignEndpoint.Constant(false), Vector(DesignEndpoint.Constant(true)))
      )
      val net = handDesign.nets.head
      rejects("duplicate")(
        handDesign.copy(nets = Vector(net.copy(loads = net.loads ++ net.loads))).bytes
      )
    }
    if args.nonEmpty then
      test("literal independent projection files match exact generated bytes") {
        val directory = Path.of(args(0))
        equalBytes(
          architecture.projection,
          Files.readAllBytes(directory.resolve("architecture.projection.json"))
        )
        equalBytes(
          exampleDesign(
            "0cbc4eb05c0f661740158587135aa55b4e03ab74f6a9e5e1dcfa95e3c42fbf9f"
          ).projection,
          Files.readAllBytes(directory.resolve("design.projection.json"))
        )
      }
    println(s"writer checks passed=$passed")
    println("This increment does not affect generated Verilog.")
