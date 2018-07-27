#!/bin/tcsh

foreach x (1 2 3 4 5 6 7 8 9 10)
  ifconfig > ifc
  if { grep xe-0 ifc } then
    break
  endif
  sleep 10
end


