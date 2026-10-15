// Included inside tb. Every record is an actual four-state case-equality check.
integer records = 0;
task observe(input string id, input [63:0] actual, input [63:0] expected);
  begin
    if ($isunknown(actual)) begin
      $display("NONBINARY\t%s\t%0t\t%h",id,$time,actual);
      $fatal(1,"non-binary-output");
    end
    $display("OBS\t%s\t%h\t%h\t%0t",id,expected,actual,$time);
    if (actual !== expected) $fatal(1,"semantic-mismatch %s time=%0t",id,$time);
    records = records + 1;
  end
endtask
