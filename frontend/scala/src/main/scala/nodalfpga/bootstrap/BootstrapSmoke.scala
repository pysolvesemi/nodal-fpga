package nodalfpga.bootstrap

/** Compiled Scala 3 witness only; no architecture DSL or generated hardware. */
object BootstrapSmoke:
  def main(args: Array[String]): Unit =
    require(args.isEmpty, "The bootstrap smoke program takes no arguments")
    println("nodal-fpga/bootstrap/1")
    println("frontend=scala3")
    println("profile=build-only")
