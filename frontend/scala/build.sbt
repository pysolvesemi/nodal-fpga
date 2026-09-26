ThisBuild / scalaVersion := "3.3.8"
ThisBuild / organization := "dev.nodalfpga"
ThisBuild / version := "0.1.0"
ThisBuild / publish / skip := true

lazy val root = project
  .in(file("."))
  .settings(
    name := "nf-frontend-bootstrap",
    scalacOptions ++= Seq("-deprecation", "-feature", "-unchecked", "-Werror", "-Wunused:all"),
    Compile / mainClass := Some("nodalfpga.bootstrap.BootstrapSmoke")
  )
